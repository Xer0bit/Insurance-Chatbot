from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CompanyInfo(Base):
    __tablename__ = 'company_info'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    contact_info = Column(String(200))

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