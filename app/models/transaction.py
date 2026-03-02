from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- IDENTIFIANT UNIQUE ---
    # Correspond au "uuid" envoyé par Flutter
    transaction_uuid = Column(String(36), unique=True, index=True, nullable=False)
    
    protocol_ver = Column(Integer, default=1)
    
    # --- PARTIES ---
    # Correspond à "sender_pk" et "receiver_pk" du Flutter
    # On garde tes noms de colonnes DB pour ne pas casser ta base existante
    sender_pubk_hash = Column(String, index=True, nullable=False) 
    receiver_pubk_hash = Column(String, index=True, nullable=False)
    
    # --- VALEUR ---
    # Correspond à "amount" du Flutter
    amount_atomic = Column(BigInteger, nullable=False)
    currency_code = Column(Integer, default=952) # 952 = XOF
    
    # --- PREUVE ---
    nonce = Column(String, nullable=False)
    signature = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    
    # --- ÉTAT & AUDIT ---
    status = Column(String, default="COMPLETED")
    is_offline_synced = Column(Boolean, default=False)
    
    # CRUCIAL : Correspond à "metadata" du Flutter. 
    # C'est ici qu'on stockera {"type": "RECHARGE"} pour l'audit.
    metadata_blob = Column(String, default="{}")