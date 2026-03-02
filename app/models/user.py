from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- IDENTITÉ (Strictement compatible avec ton App) ---
    phone_number = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    
    # SHA-256 du PIN
    pin_hash = Column(String, nullable=False)
    
    # Clé Publique (Sert d'ID unique pour la crypto)
    public_key = Column(String, unique=True, index=True, nullable=False)
    
    role = Column(String, default="USER") # USER / MERCHANT / ADMIN
    
    # Sécurité Matérielle (Device ID)
    device_hardware_id = Column(String, nullable=True)
    
    # --- FINANCE (L'Audit repose sur ces deux colonnes) ---
    # BigInteger est obligatoire pour éviter les bugs de calculs financiers
    balance_atomic = Column(BigInteger, default=0, nullable=False) # Banque
    offline_reserved_atomic = Column(BigInteger, default=0, nullable=False) # Téléphone
    
    # --- DATES ---
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())