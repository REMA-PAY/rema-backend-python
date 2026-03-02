import nacl.signing
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError 
from app.core.database import get_db

from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionBatchRequest

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/sync")
def sync_batch_transactions(batch: TransactionBatchRequest, db: Session = Depends(get_db)):
    print(f"📥 Batch de {len(batch.transactions)} txs reçu du device {batch.device_id}")
    
    report = {"processed": 0, "failed": 0, "errors": []}
    
    # 🔥 LA LISTE CRITIQUE : Le Reçu (ACK) pour le téléphone
    synced_uuids = []
    
    # 1. Vérif Marchand
    merchant = db.query(User).filter(User.public_key == batch.merchant_pk).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Marchand introuvable (PK inconnue)")

    for tx in batch.transactions:
        try:
            # 2. Idempotence (On ne traite pas deux fois le même UUID)
            exists = db.query(Transaction).filter(Transaction.transaction_uuid == tx.uuid).first()
            if exists: 
                # Si elle existe déjà, on dit au téléphone "C'est bon, je l'ai"
                # pour qu'il arrête de bloquer le solde offline.
                synced_uuids.append(tx.uuid)
                continue 

            # 3. Mouvement des fonds (Double entrée)
            sender = db.query(User).filter(User.public_key == tx.sender_pk).first()
            if sender:
                # On libère l'argent du coffre-fort hors-ligne du client
                sender.offline_reserved_atomic -= tx.amount
            
            # On crédite le marchand
            merchant.balance_atomic += tx.amount

            # 4. ARCHIVAGE DE LA PREUVE
            new_tx = Transaction(
                transaction_uuid=tx.uuid,
                protocol_ver=tx.protocol_ver,
                
                # MAPPING
                sender_pubk_hash=tx.sender_pk,      
                receiver_pubk_hash=batch.merchant_pk, 
                
                amount_atomic=tx.amount,       
                currency_code=tx.currency,
                nonce=tx.nonce,
                signature=tx.signature,
                timestamp=tx.timestamp,
                status="COMPLETED",
                is_offline_synced=True,
                
                metadata_blob=tx.metadata 
            )

            try:
                db.add(new_tx)
                db.commit() 
                report["processed"] += 1
                
                # ✅ AJOUTÉ AU REÇU POUR LE TÉLÉPHONE
                synced_uuids.append(tx.uuid) 
                
            except IntegrityError:
                db.rollback() 
                continue 

        except Exception as e:
            # On ne fait pas crasher toute la boucle si UNE transaction échoue
            report["failed"] += 1
            report["errors"].append({"uuid": tx.uuid, "msg": str(e)})

    # 5. RÉPONSE AU TÉLÉPHONE (LE FAMEUX HANDSHAKE)
    status = "success" if report["failed"] == 0 else "partial_success"
    
    return {
        "message": "Synchronisation terminée",
        "processed_count": report["processed"],
        "status": status,
        "synced_uuids": synced_uuids  # <-- Flutter va lire ça pour mettre à jour l'écran !
    }