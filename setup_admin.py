"""
Script to create the first top member/admin account
Run this once to set up your admin account
"""
from database import SessionLocal, Member, MemberType
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_admin():
    db = SessionLocal()
    
    print("Creating admin account...")
    print("Please enter admin details:")
    
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    location = input("Location (gav/mumbai): ").strip().lower()
    
    if location not in ["gav", "mumbai"]:
        location = "mumbai"
    
    # Check if admin already exists
    existing = db.query(Member).filter(Member.email == email).first()
    if existing:
        print(f"Member with email {email} already exists!")
        if input("Make this member a top member? (y/n): ").lower() == 'y':
            existing.is_top_member = True
            existing.member_type = MemberType.TOP_MEMBER
            existing.password_hash = hash_password(password)
            db.commit()
            print("Admin account updated!")
        db.close()
        return
    
    hashed_password = hash_password(password)
    
    admin = Member(
        name=name,
        email=email,
        password_hash=hashed_password,
        location=location,
        is_top_member=True,
        member_type=MemberType.TOP_MEMBER
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"\n✅ Admin account created successfully!")
    print(f"   Name: {admin.name}")
    print(f"   Email: {admin.email}")
    print(f"   Location: {admin.location}")
    print(f"\nYou can now login at http://localhost:8000")
    
    db.close()

if __name__ == "__main__":
    create_admin()

