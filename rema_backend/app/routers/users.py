from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func # Pour faire la somme (SUM)
import uuid
from typing import List

from app.core import database
from app.models.user import User 
from app.models.transaction import Transaction # Nécessaire pour créer la preuve
from app.schemas.user import RechargeRequest, RecoverRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

# --- 1. VOIR LE SOLDE ---
@router.get("/{phone}/balance")
def get_balance(phone: str, db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.phone_number == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {
        "full_name": user.full_name,
        "balance_atomic": user.balance_atomic,         
        "offline_vault_atomic": user.offline_reserved_atomic 
    }

# --- 2. RECHARGER LE TÉLÉPHONE (Avec Preuve d'Injection) ---
@router.post("/recharge-offline")
def recharge_offline(req: RechargeRequest, db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.phone_number == req.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")
    
    if user.balance_atomic < req.amount:
        raise HTTPException(status_code=400, detail="Solde bancaire insuffisant")

    # A. Mouvement des fonds
    user.balance_atomic -= req.amount          
    user.offline_reserved_atomic += req.amount 

    # B. CRÉATION DE LA PREUVE (INDISPENSABLE POUR L'AUDIT)
    # On crée une transaction "fictive" venant de la banque pour justifier l'argent
    recharge_proof = Transaction(
        transaction_uuid=str(uuid.uuid4()),
        protocol_ver=1,
        sender_pubk_hash="BANK_TREASURY", # Expéditeur Système
        receiver_pubk_hash=user.public_key,
        amount_atomic=req.amount,
        currency_code=952,
        nonce="SYSTEM_INJECTION_" + str(uuid.uuid4())[:8], 
        signature="AUTHORIZED_BY_CORE",
        timestamp=0, 
        status="COMPLETED",
        is_offline_synced=True,
        # Ce tag permet de retrouver la recharge lors de l'audit
        metadata_blob='{"type": "RECHARGE", "source": "ONLINE_BANKING"}'
    )
    db.add(recharge_proof)

    db.commit()
    db.refresh(user)
    
    return {"status": "success", "new_online_balance": user.balance_atomic}

# --- 3. RÉCUPÉRATION FORENSIQUE (Lost Device) ---
@router.post("/recover-lost-device")
def recover_lost_device(req: RecoverRequest, db: Session = Depends(database.get_db)):
    # 1. Identifier l'utilisateur
    user = db.query(User).filter(User.phone_number == req.phone).first()
    if not user: 
         raise HTTPException(status_code=403, detail="Accès refusé")
    
    print(f"🕵️ AUDIT FORENSIQUE DÉMARRÉ POUR : {user.phone_number}")

    # 2. CALCULER CE QUI A ÉTÉ INJECTÉ (TOTAL ENTRÉES)
    # Somme de tout ce qui vient de "BANK_TREASURY" vers cet utilisateur
    total_injected = db.query(func.sum(Transaction.amount_atomic))\
        .filter(Transaction.receiver_pubk_hash == user.public_key)\
        .filter(Transaction.sender_pubk_hash == "BANK_TREASURY")\
        .scalar() or 0
        
    # 3. CALCULER CE QUI A ÉTÉ DÉPENSÉ (TOTAL SORTIES PROUVÉES)
    # Somme de tout ce qui a été signé par cet utilisateur
    total_spent_proven = db.query(func.sum(Transaction.amount_atomic))\
        .filter(Transaction.sender_pubk_hash == user.public_key)\
        .scalar() or 0
        
    # 4. LE RESTE À VIVRE (MATHÉMATIQUE)
    real_remaining = total_injected - total_spent_proven
    
    if real_remaining < 0: real_remaining = 0 # Sécurité

    print(f"📊 Injecté: {total_injected} | Dépensé: {total_spent_proven} | Récupérable: {real_remaining}")

    # 5. SAUVETAGE DES FONDS (CLAWBACK)
    user.offline_reserved_atomic = 0 # Le téléphone perdu est vidé
    user.balance_atomic += real_remaining # L'argent est sécurisé en banque
    
    db.commit()
    
    return {
        "status": "success", 
        "recovered_amount": real_remaining,
        "message": f"Audit terminé. {real_remaining} FCFA ont été récupérés."
    }

# --- 4. SÉCURITÉ ---
@router.get("/security/blacklist", response_model=List[str])
def get_security_blacklist(db: Session = Depends(database.get_db)):
    return []