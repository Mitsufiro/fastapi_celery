from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

Base = declarative_base()


class Client(Base):
    __tablename__ = 'client'
    id = Column(Integer, primary_key=True)
    tel_num = Column(String)
    tag = Column(String)
    mob_code = Column(Integer)
    timezone = Column(String)


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True, index=True)
    time_created = Column(String)
    status = Column(String)
    mailing_id = Column(Integer, ForeignKey('mailinglist.id'))
    client_id = Column(Integer, ForeignKey('client.id'))

    mailing_list = relationship('MailingList')
    client = relationship('Client')


class MailingList(Base):
    __tablename__ = 'mailinglist'
    id = Column(Integer, primary_key=True, index=True)
    time_created = Column(String)
    text = Column(Text)
    tag = Column(String)
    mob_code = Column(Integer)
    time_finished = Column(String)


class Msg(Base):
    __tablename__ = 'msg'
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(Integer)
    text = Column(String)


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    access_token = Column(String)


class TokenData(Base):
    __tablename__ = 'tokendata'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    hashed_password = Column(String)
    email = Column(String)
    full_name = Column(String)
    disabled = Column(Boolean, default=False)
    role = Column(String, default='common')
