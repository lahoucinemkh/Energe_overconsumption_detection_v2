from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Time, Date
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr
from anomalyDetector import bcrypt, login_manager
from flask_login import UserMixin
from anomalyDetector.db.db import session


@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

Base = declarative_base()

class Site(Base):
    __tablename__ = 'site_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String)
    branch = Column(String)
    site_contact = Column(String)
    em = Column(String)
    winter_threshold = Column(Float)
    midseason_threshold = Column(Float)
    summer_threshold = Column(Float)
    other_threshold = Column(Float)
    margin = Column(Float)
    kw_granulation = Column(Integer)
    opening_hour_week = Column(Time) 
    closing_hour_week = Column(Time)
    opening_hour_sun = Column(Time)
    closing_hour_sun = Column(Time)
    opening_hour_other = Column(Time)
    closing_hour_other = Column(Time)
    comments = Column(String)

    meters = relationship('Meter', back_populates='site')
    anomalies = relationship('Anomaly', back_populates='site')

class Meter(Base):
    __tablename__ = 'meter_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey('site_table.id'), nullable=False)
    site_code = Column(String)
    energy_source = Column(String)
    date_time = Column(DateTime)
    real_consumption = Column(Float)
    temperature = Column(Float)
    nbmeter = Column(Integer)

    site = relationship('Site', back_populates='meters')

class Anomaly(Base):
    __tablename__ = 'anomaly_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey('site_table.id'), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    consumption_value = Column(Float)
    nbr_hour_consumption = Column(Float)
    nbr_days_consumption = Column(Integer)
    start_time = Column(Time)
    impact_consumption = Column(Float)
    period_type = Column(String)
    comments = Column(String)

    site = relationship('Site', back_populates='anomalies')
    categorization = relationship('Categorization', uselist=False, back_populates='anomaly')

class Categorization(Base):
    __tablename__ = 'categorization_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_id = Column(Integer, ForeignKey('anomaly_table.id'))
    anomaly_type = Column(String)
    category = Column(String)
    justification = Column(String)

    anomaly = relationship('Anomaly', back_populates='categorization')

class User(Base, UserMixin):
    __tablename__ = 'user_table'

    id = Column(Integer, primary_key=True)
    email_address = Column(String(length=50), nullable=False, unique=True)
    password_hash = Column(String(length=60), nullable=False)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)    
   