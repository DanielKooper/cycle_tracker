# cycle_tracker/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    partner_code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cycles = relationship('Cycle', back_populates='user')
    shared_with = relationship('PartnerShare', foreign_keys='PartnerShare.shared_by_id', back_populates='sharer')
    received_shares = relationship('PartnerShare', foreign_keys='PartnerShare.received_by_id', back_populates='receiver')

class Cycle(Base):
    __tablename__ = 'cycles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    cycle_length = Column(Integer)  # длина цикла в днях
    period_length = Column(Integer)  # длительность менструации
    
    # Симптомы и заметки
    symptoms = Column(String(500))  # JSON строка с симптомами
    mood = Column(String(50))
    flow_intensity = Column(String(20))  # light, medium, heavy
    notes = Column(String(1000))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='cycles')

class PartnerShare(Base):
    __tablename__ = 'partner_shares'
    
    id = Column(Integer, primary_key=True)
    shared_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    received_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    partner_code = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sharer = relationship('User', foreign_keys=[shared_by_id], back_populates='shared_with')
    receiver = relationship('User', foreign_keys=[received_by_id], back_populates='received_shares')

def init_db(database_url='sqlite:///cycle_tracker.db'):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def get_user_by_telegram_id(session, telegram_id):
    return session.query(User).filter_by(telegram_id=str(telegram_id)).first()

def create_user(session, telegram_id, username=None):
    user = get_user_by_telegram_id(session, telegram_id)
    if not user:
        partner_code = str(uuid.uuid4())[:8].upper()
        user = User(
            telegram_id=str(telegram_id),
            username=username,
            partner_code=partner_code
        )
        session.add(user)
        session.commit()
    return user

def add_cycle(session, user_id, start_date, **kwargs):
    cycle = Cycle(
        user_id=user_id,
        start_date=start_date,
        **kwargs
    )
    session.add(cycle)
    session.commit()
    return cycle

def get_user_cycles(session, user_id, limit=12):
    return session.query(Cycle).filter_by(user_id=user_id)\
        .order_by(Cycle.start_date.desc())\
        .limit(limit).all()

def share_partner_code(session, sharer_id, partner_code):
    """Создать связь между партнёрами"""
    receiver = session.query(User).filter_by(partner_code=partner_code).first()
    if receiver and receiver.id != sharer_id:
        # Проверяем, нет ли уже такой связи
        existing = session.query(PartnerShare).filter_by(
            shared_by_id=sharer_id,
            received_by_id=receiver.id
        ).first()
        
        if not existing:
            share = PartnerShare(
                shared_by_id=sharer_id,
                received_by_id=receiver.id,
                partner_code=partner_code
            )
            session.add(share)
            session.commit()
            return True
    return False

def get_partner_cycles(session, user_id):
    """Получить циклы партнёров"""
    shares = session.query(PartnerShare).filter_by(
        shared_by_id=user_id,
        is_active=True
    ).all()
    
    partner_data = []
    for share in shares:
        receiver = session.query(User).get(share.received_by_id)
        cycles = get_user_cycles(session, receiver.id, limit=3)
        partner_data.append({
            'username': receiver.username or 'Аноним',
            'partner_code': receiver.partner_code,
            'cycles': cycles
        })
    
    return partner_data