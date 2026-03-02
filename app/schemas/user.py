from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- CRÉATION (Input) ---
class UserCreate(BaseModel):
    phone_number: str = Field(..., description="Format international sans +")
    full_name: str
    pin_hash: str
    public_key: str # Indispensable pour l'audit futur
    role: str = "user"
    device_hardware_id: str

# --- RÉPONSE (Output) ---
class UserResponse(BaseModel):
    id: int
    phone_number: str
    full_name: str
    public_key: str  # <--- AJOUTÉ : Le téléphone a besoin de savoir sa propre clé
    is_active: bool
    created_at: datetime
    
    # Les deux soldes pour l'affichage
    balance_atomic: int      
    offline_reserved_atomic: int 

    class Config:
        from_attributes = True

# --- RECHARGE (Input) ---
class RechargeRequest(BaseModel):
    phone: str
    amount: int

# --- RÉCUPÉRATION (Input) ---
class RecoverRequest(BaseModel):
    phone: str
    # identity_proof: Optional[str] = None