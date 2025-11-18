from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
from database import (
    get_db, init_db, Member, Share, BusinessPlan, Vote, ShareAllocation,
    Proof, ProfitRecord, Transaction, MonthlyPayment,
    MemberType, BusinessPlanStatus, VoteType, ProfitAction
)

app = FastAPI(title="Fahran Business Investment System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Initialize database
init_db()

# Pydantic models
class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: str
    password: str
    introduced_by: Optional[int] = None

class MemberLogin(BaseModel):
    email: EmailStr
    password: str

class ShareCreate(BaseModel):
    share_type: str  # "base" or "additional"
    quantity: int

class BusinessPlanCreate(BaseModel):
    title: str
    description: str
    required_amount: float
    is_recurring: bool

class VoteCreate(BaseModel):
    business_plan_id: int
    vote_type: str  # "yes", "no", "abstain"

class ProfitRecordCreate(BaseModel):
    business_plan_id: int
    total_profit: float
    book_percentage: float

class ProofCreate(BaseModel):
    business_plan_id: int
    description: str
    proof_type: str

class PaymentCreate(BaseModel):
    month: int
    year: int
    amount: float

# Helper functions
def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback to bcrypt directly if passlib fails
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception:
        # Fallback to bcrypt directly if passlib fails
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_member(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    member = db.query(Member).filter(Member.email == email).first()
    if member is None:
        raise HTTPException(status_code=401, detail="Member not found")
    
    return member

def get_top_member(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Only allows top members"""
    member = get_current_member(credentials, db)
    if not member.is_top_member:
        raise HTTPException(status_code=403, detail="Only top members can access this")
    return member

# Authentication endpoints
@app.post("/api/auth/register")
def register(member_data: MemberCreate, db: Session = Depends(get_db)):
    # Check if member already exists
    existing = db.query(Member).filter(Member.email == member_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify introducer if provided
    if member_data.introduced_by:
        introducer = db.query(Member).filter(Member.id == member_data.introduced_by).first()
        if not introducer:
            raise HTTPException(status_code=400, detail="Introducer not found")
    
    hashed_password = get_password_hash(member_data.password)
    new_member = Member(
        name=member_data.name,
        email=member_data.email,
        phone=member_data.phone,
        location=member_data.location,
        password_hash=hashed_password,
        introduced_by=member_data.introduced_by,
        member_type=MemberType.NEW_MEMBER
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return {"message": "Member registered successfully", "member_id": new_member.id}

@app.post("/api/auth/login")
def login(login_data: MemberLogin, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.email == login_data.email).first()
    if not member or not verify_password(login_data.password, member.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Allow both top members and regular members to login
    # Top members get full access, regular members get limited access
    if member.member_type == MemberType.NEW_MEMBER:
        raise HTTPException(status_code=403, detail="Your account is pending approval. Please contact an admin.")
    
    access_token = create_access_token(data={"sub": member.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "member": {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "location": member.location,
            "is_top_member": member.is_top_member,
            "member_type": member.member_type.value
        }
    }

# Member endpoints
@app.get("/api/members")
def get_members(current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    members = db.query(Member).all()
    return [{
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "location": m.location,
        "member_type": m.member_type.value,
        "is_top_member": m.is_top_member
    } for m in members]

@app.get("/api/my-profile")
def get_my_profile(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """Get current logged in member's profile"""
    return {
        "id": current_member.id,
        "name": current_member.name,
        "email": current_member.email,
        "location": current_member.location,
        "member_type": current_member.member_type.value,
        "is_top_member": current_member.is_top_member
    }

@app.post("/api/members/{member_id}/approve")
def approve_member(member_id: int, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.member_type = MemberType.REGULAR_MEMBER
    db.commit()
    return {"message": "Member approved"}

# Share endpoints
@app.get("/api/my-shares")
def get_my_shares(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """Get current member's own shares"""
    shares = db.query(Share).filter(Share.member_id == current_member.id).all()
    base_shares = sum(s.quantity for s in shares if s.share_type == "base")
    additional_shares = sum(s.quantity for s in shares if s.share_type == "additional")
    
    return {
        "member_id": current_member.id,
        "member_name": current_member.name,
        "base_shares": base_shares,
        "additional_shares": additional_shares,
        "total_shares": base_shares + additional_shares,
        "base_amount": base_shares * 100,
        "additional_amount": additional_shares * 100,
        "total_amount": (base_shares + additional_shares) * 100,
        "shares": [{
            "id": s.id,
            "share_type": s.share_type,
            "quantity": s.quantity,
            "amount_per_share": s.amount_per_share,
            "total_amount": s.quantity * s.amount_per_share
        } for s in shares]
    }

@app.get("/api/shares")
def get_shares(current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    shares = db.query(Share).all()
    result = []
    for share in shares:
        member = db.query(Member).filter(Member.id == share.member_id).first()
        result.append({
            "id": share.id,
            "member_id": share.member_id,
            "member_name": member.name if member else "Unknown",
            "share_type": share.share_type,
            "quantity": share.quantity,
            "amount_per_share": share.amount_per_share,
            "total_amount": share.quantity * share.amount_per_share
        })
    return result

@app.get("/api/members/{member_id}/shares")
def get_member_shares(member_id: int, current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    # Regular members can only view their own shares
    if not current_member.is_top_member and current_member.id != member_id:
        raise HTTPException(status_code=403, detail="You can only view your own shares")
    shares = db.query(Share).filter(Share.member_id == member_id).all()
    base_shares = sum(s.quantity for s in shares if s.share_type == "base")
    additional_shares = sum(s.quantity for s in shares if s.share_type == "additional")
    
    return {
        "member_id": member_id,
        "base_shares": base_shares,
        "additional_shares": additional_shares,
        "total_shares": base_shares + additional_shares,
        "base_amount": base_shares * 100,
        "additional_amount": additional_shares * 100,
        "total_amount": (base_shares + additional_shares) * 100
    }

@app.post("/api/members/{member_id}/shares")
def create_share(member_id: int, share_data: ShareCreate, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if base share already exists
    if share_data.share_type == "base":
        existing = db.query(Share).filter(
            and_(Share.member_id == member_id, Share.share_type == "base")
        ).first()
        if existing:
            existing.quantity += share_data.quantity
            db.commit()
            return {"message": "Base shares updated", "share_id": existing.id}
    
    new_share = Share(
        member_id=member_id,
        share_type=share_data.share_type,
        quantity=share_data.quantity,
        amount_per_share=100.0
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    return {"message": "Share created", "share_id": new_share.id}

# Business Plan endpoints
@app.get("/api/business-plans")
def get_business_plans(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    # All members can view business plans
    plans = db.query(BusinessPlan).order_by(BusinessPlan.created_at.desc()).all()
    result = []
    for plan in plans:
        proposer = db.query(Member).filter(Member.id == plan.proposer_id).first()
        votes = db.query(Vote).filter(Vote.business_plan_id == plan.id).all()
        yes_votes = sum(1 for v in votes if v.vote_type == VoteType.YES)
        no_votes = sum(1 for v in votes if v.vote_type == VoteType.NO)
        
        result.append({
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "proposer_id": plan.proposer_id,
            "proposer_name": proposer.name if proposer else "Unknown",
            "required_amount": plan.required_amount,
            "funded_amount": plan.funded_amount,
            "is_recurring": plan.is_recurring,
            "status": plan.status.value,
            "voting_start": plan.voting_start.isoformat() if plan.voting_start else None,
            "voting_end": plan.voting_end.isoformat() if plan.voting_end else None,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "total_votes": len(votes),
            "current_profit": plan.current_profit,
            "total_loss": plan.total_loss
        })
    return result

@app.post("/api/business-plans")
def create_business_plan(plan_data: BusinessPlanCreate, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    voting_end = datetime.utcnow() + timedelta(days=3)
    
    new_plan = BusinessPlan(
        title=plan_data.title,
        description=plan_data.description,
        proposer_id=current_member.id,
        required_amount=plan_data.required_amount,
        is_recurring=plan_data.is_recurring,
        status=BusinessPlanStatus.PENDING_VOTE,
        voting_start=datetime.utcnow(),
        voting_end=voting_end
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"message": "Business plan created", "plan_id": new_plan.id}

@app.post("/api/business-plans/{plan_id}/vote")
def vote_on_plan(plan_id: int, vote_data: VoteCreate, current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Business plan not found")
    
    if plan.status != BusinessPlanStatus.PENDING_VOTE:
        raise HTTPException(status_code=400, detail="Voting period has ended")
    
    if datetime.utcnow() > plan.voting_end:
        raise HTTPException(status_code=400, detail="Voting period has expired")
    
    # Check if already voted
    existing_vote = db.query(Vote).filter(
        and_(Vote.member_id == current_member.id, Vote.business_plan_id == plan_id)
    ).first()
    
    if existing_vote:
        existing_vote.vote_type = VoteType(vote_data.vote_type)
        existing_vote.voted_at = datetime.utcnow()
    else:
        new_vote = Vote(
            member_id=current_member.id,
            business_plan_id=plan_id,
            vote_type=VoteType(vote_data.vote_type)
        )
        db.add(new_vote)
    
    db.commit()
    
    # Check if voting period ended and process results
    check_and_process_voting(plan_id, db)
    
    return {"message": "Vote recorded"}

def check_and_process_voting(plan_id: int, db: Session):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if not plan or datetime.utcnow() < plan.voting_end:
        return
    
    votes = db.query(Vote).filter(Vote.business_plan_id == plan_id).all()
    yes_votes = sum(1 for v in votes if v.vote_type == VoteType.YES)
    no_votes = sum(1 for v in votes if v.vote_type == VoteType.NO)
    total_members = db.query(Member).filter(Member.member_type != MemberType.NEW_MEMBER).count()
    
    # Auto-vote for non-voters (minimum share criteria)
    non_voters = db.query(Member).filter(
        and_(
            Member.member_type != MemberType.NEW_MEMBER,
            ~Member.id.in_([v.member_id for v in votes])
        )
    ).all()
    
    for member in non_voters:
        # Apply minimum share criteria (auto yes vote)
        auto_vote = Vote(
            member_id=member.id,
            business_plan_id=plan_id,
            vote_type=VoteType.YES
        )
        db.add(auto_vote)
        yes_votes += 1
    
    db.commit()
    
    # Check majority
    total_votes_after_auto = yes_votes + no_votes
    if yes_votes > no_votes and yes_votes > total_votes_after_auto / 2:
        plan.status = BusinessPlanStatus.FUNDING_ROUND_1
        process_funding_round(plan_id, db)
    else:
        plan.status = BusinessPlanStatus.REJECTED
    
    db.commit()

def process_funding_round(plan_id: int, db: Session):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if not plan:
        return
    
    total_shares_needed = int(plan.required_amount / 100)
    yes_voters = db.query(Member).join(Vote).filter(
        and_(
            Vote.business_plan_id == plan_id,
            Vote.vote_type == VoteType.YES
        )
    ).all()
    
    if not yes_voters:
        return
    
    # Scenario 1: All voted yes
    if len(yes_voters) == db.query(Member).filter(Member.member_type != MemberType.NEW_MEMBER).count():
        min_shares_per_person = total_shares_needed // len(yes_voters)
        allocate_shares_scenario1(plan_id, min_shares_per_person, db)
    else:
        # Scenario 2: Partial yes votes
        allocate_shares_scenario2(plan_id, db)

def allocate_shares_scenario1(plan_id: int, min_shares: int, db: Session):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    yes_voters = db.query(Member).join(Vote).filter(
        and_(
            Vote.business_plan_id == plan_id,
            Vote.vote_type == VoteType.YES
        )
    ).all()
    
    for member in yes_voters:
        base_shares = db.query(Share).filter(
            and_(Share.member_id == member.id, Share.share_type == "base")
        ).first()
        
        if base_shares and base_shares.quantity >= min_shares:
            allocate_amount = min_shares * 100
        else:
            available_base = base_shares.quantity if base_shares else 0
            allocate_amount = available_base * 100
        
        if allocate_amount > 0:
            allocation = ShareAllocation(
                business_plan_id=plan_id,
                member_id=member.id,
                share_type="base",
                quantity=int(allocate_amount / 100),
                amount=allocate_amount
            )
            db.add(allocation)
    
    db.commit()
    # Start round 2 if needed
    check_funding_completion(plan_id, db)

def allocate_shares_scenario2(plan_id: int, db: Session):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    yes_voters = db.query(Member).join(Vote).filter(
        and_(
            Vote.business_plan_id == plan_id,
            Vote.vote_type == VoteType.YES
        )
    ).all()
    
    total_shares_needed = int(plan.required_amount / 100)
    allocated_shares = 0
    
    # Round 1: Allocate from yes voters
    for member in yes_voters:
        base_shares = db.query(Share).filter(
            and_(Share.member_id == member.id, Share.share_type == "base")
        ).first()
        
        if base_shares and base_shares.quantity > 0:
            if not plan.is_recurring:
                additional_shares = db.query(Share).filter(
                    and_(Share.member_id == member.id, Share.share_type == "additional")
                ).first()
                available = (base_shares.quantity if base_shares else 0) + (additional_shares.quantity if additional_shares else 0)
            else:
                available = base_shares.quantity
            
            if allocated_shares < total_shares_needed:
                to_allocate = min(available, total_shares_needed - allocated_shares)
                allocated_shares += to_allocate
                
                allocation = ShareAllocation(
                    business_plan_id=plan_id,
                    member_id=member.id,
                    share_type="base" if plan.is_recurring else "mixed",
                    quantity=to_allocate,
                    amount=to_allocate * 100
                )
                db.add(allocation)
    
    db.commit()
    plan.status = BusinessPlanStatus.FUNDING_ROUND_2
    db.commit()
    
    # Round 2: Open to all members
    if allocated_shares < total_shares_needed:
        all_members = db.query(Member).filter(Member.member_type != MemberType.NEW_MEMBER).all()
        for member in all_members:
            if allocated_shares >= total_shares_needed:
                break
            
            base_shares = db.query(Share).filter(
                and_(Share.member_id == member.id, Share.share_type == "base")
            ).first()
            
            if not plan.is_recurring:
                additional_shares = db.query(Share).filter(
                    and_(Share.member_id == member.id, Share.share_type == "additional")
                ).first()
                available = (base_shares.quantity if base_shares else 0) + (additional_shares.quantity if additional_shares else 0)
            else:
                available = base_shares.quantity if base_shares else 0
            
            if available > 0:
                to_allocate = min(available, total_shares_needed - allocated_shares)
                allocated_shares += to_allocate
                
                allocation = ShareAllocation(
                    business_plan_id=plan_id,
                    member_id=member.id,
                    share_type="base" if plan.is_recurring else "mixed",
                    quantity=to_allocate,
                    amount=to_allocate * 100
                )
                db.add(allocation)
    
    db.commit()
    check_funding_completion(plan_id, db)

def check_funding_completion(plan_id: int, db: Session):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    allocations = db.query(ShareAllocation).filter(ShareAllocation.business_plan_id == plan_id).all()
    total_funded = sum(a.amount for a in allocations)
    plan.funded_amount = total_funded
    
    if total_funded >= plan.required_amount:
        plan.status = BusinessPlanStatus.ACTIVE
    else:
        plan.status = BusinessPlanStatus.ACTIVE  # Still active with partial funding
    
    db.commit()

@app.post("/api/business-plans/{plan_id}/profit")
def record_profit(plan_id: int, profit_data: ProfitRecordCreate, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Business plan not found")
    
    booked_amount = profit_data.total_profit * (profit_data.book_percentage / 100)
    carry_forward = profit_data.total_profit - booked_amount
    
    profit_record = ProfitRecord(
        business_plan_id=plan_id,
        total_profit=profit_data.total_profit,
        book_percentage=profit_data.book_percentage,
        booked_amount=booked_amount,
        carry_forward_amount=carry_forward,
        voting_result=ProfitAction.PARTIAL if profit_data.book_percentage < 100 else ProfitAction.BOOK
    )
    db.add(profit_record)
    
    plan.current_profit += profit_data.total_profit
    
    # Distribute profit to members
    allocations = db.query(ShareAllocation).filter(ShareAllocation.business_plan_id == plan_id).all()
    total_shares = sum(a.quantity for a in allocations)
    
    for allocation in allocations:
        member_profit_share = (allocation.quantity / total_shares) * profit_data.total_profit
        member_booked = member_profit_share * (profit_data.book_percentage / 100)
        member_carry_forward = member_profit_share - member_booked
        
        # Create transaction for booked profit
        if member_booked > 0:
            transaction = Transaction(
                member_id=allocation.member_id,
                transaction_type="profit",
                amount=member_booked,
                description=f"Profit from {plan.title}",
                business_plan_id=plan_id
            )
            db.add(transaction)
        
        # Convert carry forward to additional shares
        if member_carry_forward > 0:
            additional_shares_qty = int(member_carry_forward / 100)
            remainder = member_carry_forward % 100
            
            if additional_shares_qty > 0:
                existing_additional = db.query(Share).filter(
                    and_(Share.member_id == allocation.member_id, Share.share_type == "additional")
                ).first()
                
                if existing_additional:
                    existing_additional.quantity += additional_shares_qty
                else:
                    new_share = Share(
                        member_id=allocation.member_id,
                        share_type="additional",
                        quantity=additional_shares_qty,
                        amount_per_share=100.0
                    )
                    db.add(new_share)
            
            # Return remainder as cash
            if remainder > 0:
                transaction = Transaction(
                    member_id=allocation.member_id,
                    transaction_type="profit",
                    amount=remainder,
                    description=f"Profit remainder from {plan.title}",
                    business_plan_id=plan_id
                )
                db.add(transaction)
    
    # Proposer gets 10% of total profit
    proposer_profit = profit_data.total_profit * 0.10
    proposer_transaction = Transaction(
        member_id=plan.proposer_id,
        transaction_type="profit",
        amount=proposer_profit,
        description=f"Proposer bonus from {plan.title}",
        business_plan_id=plan_id
    )
    db.add(proposer_transaction)
    
    db.commit()
    return {"message": "Profit recorded and distributed"}

@app.post("/api/business-plans/{plan_id}/proofs")
def add_proof(plan_id: int, proof_data: ProofCreate, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    plan = db.query(BusinessPlan).filter(BusinessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Business plan not found")
    
    new_proof = Proof(
        business_plan_id=plan_id,
        description=proof_data.description,
        proof_type=proof_data.proof_type
    )
    db.add(new_proof)
    db.commit()
    return {"message": "Proof added"}

# Payment endpoints
@app.post("/api/members/{member_id}/payments")
def record_payment(member_id: int, payment_data: PaymentCreate, current_member: Member = Depends(get_top_member), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    base_shares = db.query(Share).filter(
        and_(Share.member_id == member_id, Share.share_type == "base")
    ).first()
    
    shares_count = base_shares.quantity if base_shares else 0
    amount_due = shares_count * 100
    
    payment = MonthlyPayment(
        member_id=member_id,
        month=payment_data.month,
        year=payment_data.year,
        base_shares_count=shares_count,
        amount_due=amount_due,
        amount_paid=payment_data.amount,
        is_paid=payment_data.amount >= amount_due,
        paid_at=datetime.utcnow() if payment_data.amount >= amount_due else None
    )
    db.add(payment)
    
    if base_shares:
        base_shares.last_payment_date = datetime.utcnow()
    
    transaction = Transaction(
        member_id=member_id,
        transaction_type="share_payment",
        amount=payment_data.amount,
        description=f"Monthly payment for {payment_data.month}/{payment_data.year}"
    )
    db.add(transaction)
    
    db.commit()
    return {"message": "Payment recorded"}

# Reports
@app.get("/api/my-statement")
def get_my_statement(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """Get current member's own statement"""
    member_id = current_member.id
    member = current_member
    
    shares = db.query(Share).filter(Share.member_id == member_id).all()
    allocations = db.query(ShareAllocation).filter(ShareAllocation.member_id == member_id).all()
    transactions = db.query(Transaction).filter(Transaction.member_id == member_id).order_by(Transaction.transaction_date.desc()).all()
    
    base_shares = sum(s.quantity for s in shares if s.share_type == "base")
    additional_shares = sum(s.quantity for s in shares if s.share_type == "additional")
    
    return {
        "member": {
            "id": member.id,
            "name": member.name,
            "email": member.email
        },
        "shares": {
            "base": base_shares,
            "additional": additional_shares,
            "total": base_shares + additional_shares
        },
        "allocations": [{
            "plan_id": a.business_plan_id,
            "quantity": a.quantity,
            "amount": a.amount,
            "share_type": a.share_type
        } for a in allocations],
        "transactions": [{
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "description": t.description,
            "date": t.transaction_date.isoformat()
        } for t in transactions]
    }

@app.get("/api/members/{member_id}/statement")
def get_member_statement(member_id: int, current_member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    # Regular members can only view their own statement
    if not current_member.is_top_member and current_member.id != member_id:
        raise HTTPException(status_code=403, detail="You can only view your own statement")
    
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    shares = db.query(Share).filter(Share.member_id == member_id).all()
    allocations = db.query(ShareAllocation).filter(ShareAllocation.member_id == member_id).all()
    transactions = db.query(Transaction).filter(Transaction.member_id == member_id).order_by(Transaction.transaction_date.desc()).all()
    
    base_shares = sum(s.quantity for s in shares if s.share_type == "base")
    additional_shares = sum(s.quantity for s in shares if s.share_type == "additional")
    
    return {
        "member": {
            "id": member.id,
            "name": member.name,
            "email": member.email
        },
        "shares": {
            "base": base_shares,
            "additional": additional_shares,
            "total": base_shares + additional_shares
        },
        "allocations": [{
            "plan_id": a.business_plan_id,
            "quantity": a.quantity,
            "amount": a.amount,
            "share_type": a.share_type
        } for a in allocations],
        "transactions": [{
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "description": t.description,
            "date": t.transaction_date.isoformat()
        } for t in transactions]
    }

# Serve frontend
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    # If static directory doesn't exist, create it
    import os
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

