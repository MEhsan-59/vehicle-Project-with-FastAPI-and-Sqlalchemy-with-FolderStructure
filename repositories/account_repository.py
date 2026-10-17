from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import Base
from models.user import Account
from core.security import SecurityHelper


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, user_name: str, password: str):
        if self.get_by_user_id(user_id) is not None:
            return None

        hashed_password = SecurityHelper.hash_password(password)
        account = Account(user_id=user_id, user_name=user_name, password=hashed_password)
        try:
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            return account
        except IntegrityError:
            self.db.rollback()
            return None

    def get_by_user_id(self, user_id: str):
        return self.db.query(Account).filter(Account.user_id == user_id).first()

    def validate_login(self, user_id: str, password: str):
        account = self.get_by_user_id(user_id)
        if account is None:
            return None

        if not SecurityHelper.verify_password(password, account.password):
            return None

        return account
