from pydantic import BaseModel
from typing import List, Optional

# --- UNE TRANSACTION UNIQUE (Telle qu'envoyée par Flutter) ---
class SingleTransaction(BaseModel):
    uuid: str           
    protocol_ver: int   
    nonce: str          
    timestamp: int      
    sender_pk: str      # Flutter envoie "sender_pk"
    receiver_pk: str    # Flutter envoie "receiver_pk"
    amount: int         
    currency: int       
    signature: str      
    
    # Le type est souvent "OFFLINE_PAYMENT"
    type: str = "OFFLINE_PAYMENT"
    
    # C'est ici qu'on reçoit le JSON stringifié {"type": "RECHARGE"} pour l'audit
    metadata: Optional[str] = "{}" 

# --- LE BATCH DE SYNCHRONISATION (Le paquet complet) ---
class TransactionBatchRequest(BaseModel):
    merchant_pk: str        
    batch_id: str
    device_id: str
    count: int
    sync_timestamp: str
    
    # La liste des transactions ci-dessus
    transactions: List[SingleTransaction]

# --- RÉPONSES UTILITAIRES ---
class TransactionResponse(BaseModel):
    status: str
    message: str

class SignedPayload(BaseModel):
    payload: str
    signature: str