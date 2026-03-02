import nacl.signing
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError 
from app.core.database import get_db

from app.models.transaction import Transaction
from app.models.user import User

# ✅ IMPORT CORRIGÉ ET VALIDÉ
from app.schemas.transaction import TransactionBatchRequest

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/sync")
def sync_batch_transactions(batch: TransactionBatchRequest, db: Session = Depends(get_db)):
    print(f"📥 Batch de {len(batch.transactions)} txs reçu du device {batch.device_id}")
    
    report = {"processed": 0, "failed": 0, "errors": [], "status": "partial_success"}
    
    # 1. Vérif Marchand
    merchant = db.query(User).filter(User.public_key == batch.merchant_pk).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Marchand introuvable (PK inconnue)")

    for tx in batch.transactions:
        try:
            # 2. Idempotence (On ne traite pas deux fois le même UUID)
            exists = db.query(Transaction).filter(Transaction.transaction_uuid == tx.uuid).first()
            if exists: 
                continue 

            # 3. Anti-Rejeu (Le Nonce protège contre la duplication cryptographique)
            nonce_exists = db.query(Transaction).filter(Transaction.nonce == tx.nonce).first()
            if nonce_exists: 
                continue

            # 4. Accounting (Mise à jour des soldes "theoriques" pour affichage)
            # Note: Le vrai solde est calculé par Audit, mais on met à jour pour l'UI
            sender = db.query(User).filter(User.public_key == tx.sender_pk).first()
            if sender: 
                sender.offline_reserved_atomic -= tx.amount
            
            merchant.balance_atomic += tx.amount

            # 5. ARCHIVAGE (CRITIQUE)
            new_tx = Transaction(
                transaction_uuid=tx.uuid,
                protocol_ver=tx.protocol_ver,
                
                # MAPPING SCHEMA -> MODEL
                sender_pubk_hash=tx.sender_pk,      # Schema: sender_pk -> Model: sender_pubk_hash
                receiver_pubk_hash=batch.merchant_pk, # Le receiver est le marchand qui sync
                
                amount_atomic=tx.amount,       
                currency_code=tx.currency,
                nonce=tx.nonce,
                signature=tx.signature,
                timestamp=tx.timestamp,
                status="COMPLETED",
                is_offline_synced=True,
                
                # 🔥 C'EST ICI QUE TOUT SE JOUE POUR L'AUDIT
                metadata_blob=tx.metadata 
            )

            try:
                db.add(new_tx)
                db.commit() 
                report["processed"] += 1
            except IntegrityError:
                db.rollback() 
                continue 

        except Exception as e:
            # On ne plante pas tout le batch pour une erreur
            report["failed"] += 1
            report["errors"].append({"uuid": tx.uuid, "msg": str(e)})

    report["status"] = "success" if report["failed"] == 0 else "partial_success"
    return report