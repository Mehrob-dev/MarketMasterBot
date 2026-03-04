from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from db import Users, engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(engine)


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        session = Session()

        user = session.query(Users).filter_by(
            tg_id=event.from_user.id
        ).first()

        if user and user.is_admin:
            return True

        return False