from sqlalchemy.orm import relationship, backref, joinedload
from sqlalchemy import Column, DateTime, String, Integer, Float, ForeignKey, func
from .base import Base, inverse_relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    fullname = Column(String, nullable=False)
    hashed_pw = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Show(Base):
    __tablename__ = 'shows'
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True)
    title = Column(String, nullable=False)
    image_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Like(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    show_id = Column(Integer, ForeignKey('shows.id'))

    user = relationship('User', backref=inverse_relationship('likes'))
    show = relationship('Show', backref=inverse_relationship('likes'))
