from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User


class IAuthRepository(ABC):
    """Contrato para operaciones de autenticación y gestión de usuarios."""

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    @abstractmethod
    def create(self, user: User) -> User:
        ...

    @abstractmethod
    def update_last_access(self, user_id: int) -> None:
        ...

    @abstractmethod
    def username_exists(self, username: str) -> bool:
        ...

    @abstractmethod
    def email_exists(self, email: str) -> bool:
        ...
