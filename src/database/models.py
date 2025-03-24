from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CompanyInfo(Base):
    __tablename__ = 'company_info'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    contact_info = Column(String(200))

class ContactForm(Base):
    __tablename__ = 'contact_forms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    message = Column(Text)
    submission_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='new')

class InsurancePolicy:
    def __init__(self, policy_id, policy_holder_name, insurance_type, start_date, end_date):
        self.policy_id = policy_id
        self.policy_holder_name = policy_holder_name
        self.insurance_type = insurance_type
        self.start_date = start_date
        self.end_date = end_date

class Customer:
    def __init__(self, customer_id, name, email, phone):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone

class MeetingSchedule:
    def __init__(self, meeting_id, customer_id, suggested_time, meeting_type):
        self.meeting_id = meeting_id
        self.customer_id = customer_id
        self.suggested_time = suggested_time
        self.meeting_type = meeting_type