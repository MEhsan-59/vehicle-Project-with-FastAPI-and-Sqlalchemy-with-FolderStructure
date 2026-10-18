from core.auth import create_access_token
from repositories.account_repository import AccountRepository


class AccountManager:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def create_account(self, user_id: str, user_name: str, password: str):
        existing = self.repository.get_by_user_id(user_id)
        if existing is not None:
            return {"status": False, "message": "Account already exists."}

        user = self.repository.create(user_id, user_name, password)
        if user is None:
            return {"status": False, "message": "Account creation failed."}

        return {"status": True, "message": "Account Successfully created."}

    def login_account(self, user_id: str, password: str):
        account = self.repository.validate_login(user_id, password)
        if account is None:
            return {"status": False, "message": "Invalid user_id or password"}

        token = create_access_token(account.user_id)
        return {
            "status": True,
            "message": "Account login successfully.",
            "access_token": token,
            "token_type": "bearer",
        }

    def get_account_by_id(self, user_id: str):
        return self.repository.get_by_user_id(user_id)

    def verify_password(self, user_id: str, password: str) -> bool:
        return self.repository.validate_login(user_id, password) is not None
