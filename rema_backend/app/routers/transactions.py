import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionBatchRequest, SingleTransaction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _tx_already_exists(db: Session, tx: SingleTransaction) -> bool:
    """Skip if UUID or nonce already recorded (idempotence + anti-replay)."""
    return (
        db.query(Transaction.id).filter(Transaction.transaction_uuid == tx.uuid).first() is not None
        or db.query(Transaction.id).filter(Transaction.nonce == tx.nonce).first() is not None
    )


def _update_balances(sender: User | None, merchant: User, amount: int) -> None:
    """Adjust cached balances for UI display (real balance is computed by audit)."""
    if sender:
        sender.offline_reserved_atomic -= amount
    merchant.balance_atomic += amount


def _build_transaction(tx: SingleTransaction, merchant_pk: str) -> Transaction:
    return Transaction(
        transaction_uuid=tx.uuid,
        protocol_ver=tx.protocol_ver,
        sender_pubk_hash=tx.sender_pk,
        receiver_pubk_hash=merchant_pk,
        amount_atomic=tx.amount,
        currency_code=tx.currency,
        nonce=tx.nonce,
        signature=tx.signature,
        timestamp=tx.timestamp,
        status="COMPLETED",
        is_offline_synced=True,
        metadata_blob=tx.metadata,
    )


def _process_single_tx(
    tx: SingleTransaction,
    merchant: User,
    db: Session,
) -> bool:
    """Process one transaction. Returns True on success, False on skip/duplicate."""
    if _tx_already_exists(db, tx):
        return False

    sender = db.query(User).filter(User.public_key == tx.sender_pk).first()
    _update_balances(sender, merchant, tx.amount)

    new_tx = _build_transaction(tx, merchant.public_key)
    db.add(new_tx)
    db.commit()
    return True


@router.post("/sync")
def sync_batch_transactions(
    batch: TransactionBatchRequest,
    db: Session = Depends(get_db),
):
    logger.info("Batch of %d txs received from device %s", len(batch.transactions), batch.device_id)

    merchant = db.query(User).filter(User.public_key == batch.merchant_pk).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Marchand introuvable (PK inconnue)")

    report: dict = {"processed": 0, "failed": 0, "errors": [], "status": "partial_success"}

    for tx in batch.transactions:
        try:
            if _process_single_tx(tx, merchant, db):
                report["processed"] += 1
        except IntegrityError:
            db.rollback()
        except Exception as e:
            report["failed"] += 1
            report["errors"].append({"uuid": tx.uuid, "msg": str(e)})

    report["status"] = "success" if report["failed"] == 0 else "partial_success"
    return report
