import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import backref

from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin



class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    text = sa.Column(sa.Text, nullable=True)
    response_to = sa.Column(sa.Integer, sa.ForeignKey("chats.id"), nullable=True) #указывает на id этой же таблицы
    create_date = sa.Column(sa.DateTime, nullable=True, default=datetime.datetime.now())
    section_id = sa.Column(sa.Integer, sa.ForeignKey("sections.id"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))

    parent_msg = orm.relationship('Chat', remote_side=[id])
    user = orm.relation('User')
    section = orm.relation('Section', back_populates="chats")
    