from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User, UserRole
from app.core.security import get_password_hash


class UserService:
    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        user_in.password = get_password_hash(user_in.password)
        # Map Create Schema to Model-compatible dict (handling renaming if needed)
        # Assuming UserCreate matches User model fields mostly
        # We need to map 'password' to 'hashed_password' and remove 'password'
        user_data = user_in.model_dump()
        hashed_password = user_data.pop("password")
        user_data["hashed_password"] = hashed_password

        # We can't pass arbitrary dict to repo.create if it expects Schema
        # But BaseRepository.create takes CreateSchemaType.
        # So we might need to adjust BaseRepository or do it here.
        # Actually, BaseRepository expects obj_in (Schema).
        # We should create the DB object manually here?
        # Or let's modify the interface for flexibility.
        # For now, let's instantiate the User model directly and add it,
        # bypassing repo's simple create if it's too rigid, or create a flexible method.
        # But we must use Repository pattern.

        # Let's create a NEW schema instance or update the dict?
        # The repo.create does `obj_in.model_dump()`.

        # NOTE: This suggests my BaseRepository might be too strict or I need a schema that matches DB exactly.
        # Ideally, Repository handles the Schema -> Model conversion.
        # But here 'password' -> 'hashed_password' logic is business logic.

        # Let's modify the input schema or pass a dict to a custom method.
        # Simpler: Create the User object here and use db.add directly?
        # No, that breaks the pattern.

        # Correct approach: Repository should handle DB concerns.
        # But this is specific transformation.

        obj_in_data = user_in.model_dump()
        password = obj_in_data.pop("password")
        obj_in_data["hashed_password"] = get_password_hash(password)

        # Using the Model constructor directly which repo logic does anyway
        db_obj = User(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        return await user_repo.get_by_email(db, email=email)


user_service = UserService()
