from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class MemberType(enum.Enum):
    TOP_MEMBER = "top_member"
    REGULAR_MEMBER = "regular_member"
    NEW_MEMBER = "new_member"

class BusinessPlanStatus(enum.Enum):
    PENDING_VOTE = "pending_vote"
    APPROVED = "approved"
    REJECTED = "rejected"
    FUNDING_ROUND_1 = "funding_round_1"
    FUNDING_ROUND_2 = "funding_round_2"
    ACTIVE = "active"
    COMPLETED = "completed"

class VoteType(enum.Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"

class ProfitAction(enum.Enum):
    BOOK = "book"
    CARRY_FORWARD = "carry_forward"
    PARTIAL = "partial"

class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    location = Column(String)  # "gav" or "mumbai"
    password_hash = Column(String)
    member_type = Column(SQLEnum(MemberType), default=MemberType.REGULAR_MEMBER)
    is_top_member = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    introduced_by = Column(Integer, ForeignKey("members.id"), nullable=True)
    
    # Relationships
    base_shares = relationship("Share", foreign_keys="Share.member_id", back_populates="member")
    votes = relationship("Vote", back_populates="member")
    business_plans = relationship("BusinessPlan", back_populates="proposer")
    transactions = relationship("Transaction", back_populates="member")

class Share(Base):
    __tablename__ = "shares"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    share_type = Column(String)  # "base" or "additional"
    quantity = Column(Integer, default=0)
    amount_per_share = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_payment_date = Column(DateTime)
    
    # Relationships
    member = relationship("Member", back_populates="base_shares")
    allocations = relationship("ShareAllocation", back_populates="share")

class BusinessPlan(Base):
    __tablename__ = "business_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    proposer_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    required_amount = Column(Float, nullable=False)
    is_recurring = Column(Boolean, default=False)  # True for base shares only, False for both
    status = Column(SQLEnum(BusinessPlanStatus), default=BusinessPlanStatus.PENDING_VOTE)
    voting_start = Column(DateTime, default=datetime.utcnow)
    voting_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    funded_amount = Column(Float, default=0.0)
    current_profit = Column(Float, default=0.0)
    total_loss = Column(Float, default=0.0)
    
    # Relationships
    proposer = relationship("Member", back_populates="business_plans")
    votes = relationship("Vote", back_populates="business_plan")
    allocations = relationship("ShareAllocation", back_populates="business_plan")
    proofs = relationship("Proof", back_populates="business_plan")
    profit_records = relationship("ProfitRecord", back_populates="business_plan")

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    business_plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=False)
    vote_type = Column(SQLEnum(VoteType), nullable=False)
    voted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship("Member", back_populates="votes")
    business_plan = relationship("BusinessPlan", back_populates="votes")

class ShareAllocation(Base):
    __tablename__ = "share_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=True)
    share_type = Column(String)  # "base" or "additional"
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business_plan = relationship("BusinessPlan", back_populates="allocations")
    share = relationship("Share", back_populates="allocations")

class Proof(Base):
    __tablename__ = "proofs"
    
    id = Column(Integer, primary_key=True, index=True)
    business_plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=False)
    description = Column(Text)
    proof_type = Column(String)  # "receipt", "transaction", "other"
    file_path = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    verified_by = Column(Integer, ForeignKey("members.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    business_plan = relationship("BusinessPlan", back_populates="proofs")

class ProfitRecord(Base):
    __tablename__ = "profit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    business_plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=False)
    total_profit = Column(Float, nullable=False)
    book_percentage = Column(Float, default=0.0)  # Percentage to book
    booked_amount = Column(Float, default=0.0)
    carry_forward_amount = Column(Float, default=0.0)
    voting_result = Column(SQLEnum(ProfitAction))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business_plan = relationship("BusinessPlan", back_populates="profit_records")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    transaction_type = Column(String)  # "share_payment", "profit", "withdrawal", "additional_share"
    amount = Column(Float, nullable=False)
    description = Column(Text)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    business_plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=True)
    
    # Relationships
    member = relationship("Member", back_populates="transactions")

class MonthlyPayment(Base):
    __tablename__ = "monthly_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    base_shares_count = Column(Integer, default=0)
    amount_due = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    paid_at = Column(DateTime, nullable=True)
    is_paid = Column(Boolean, default=False)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./fahran_business.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

