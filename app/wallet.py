from sqlalchemy.orm import Session
from app.models import User, WalletTransaction

def get_balance(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    return user.wallet if user else 0.0

def credit(db: Session, user_id: int, amount: float, reason: str):
    user = db.query(User).filter(User.id == user_id).first()
    user.wallet += amount
    db.add(WalletTransaction(user_id=user_id, amount=amount, reason=reason))
    db.commit()

def debit(db: Session, user_id: int, amount: float, reason: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user.wallet < amount:
        return False
    user.wallet -= amount
    db.add(WalletTransaction(user_id=user_id, amount=-amount, reason=reason))
    db.commit()
    return True
