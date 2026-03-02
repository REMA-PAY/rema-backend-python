# app/schemas/__init__.py

# 1. Transactions (Batch & Payload + SingleTransaction)
# J'ai ajouté SingleTransaction car il est utilisé dans le Batch
from .transaction import (
    TransactionBatchRequest, 
    TransactionResponse, 
    SignedPayload, 
    SingleTransaction
)

# 2. Authentification (JWT)
# (Je suppose que token.py existe déjà chez toi)
from .token import Token, TokenData

# 3. Utilisateurs & Actions Financières
# 🔥 IL MANQUAIT RechargeRequest et RecoverRequest ICI !
from .user import (
    UserCreate, 
    UserResponse, 
    RechargeRequest, 
    RecoverRequest
)