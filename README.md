# Fahran Business Investment System

A comprehensive share-based investment platform built with Python FastAPI and HTML/CSS/JavaScript.

## Features

- **Member Management**: Register and manage members (top members can login)
- **Share System**: 
  - Base shares (monthly recurring payments)
  - Additional shares (one-time purchases)
- **Business Plans**: Create, vote, and fund business plans
- **Voting System**: 3-day voting period with automatic processing
- **Funding Rounds**: Automatic share allocation based on voting results
- **Profit Management**: Book profits or carry forward to additional shares
- **Payment Tracking**: Monthly payment tracking for base shares
- **Reports**: Member statements and transaction history

## Tech Stack

- **Backend**: Python 3.9+, FastAPI
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT tokens

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python -c "from database import init_db; init_db()"
```

4. Create a top member (you'll need to do this manually in the database or via API):
```python
from database import SessionLocal, Member, MemberType
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

top_member = Member(
    name="Admin",
    email="admin@example.com",
    password_hash=pwd_context.hash("your_password"),
    location="mumbai",
    is_top_member=True,
    member_type=MemberType.TOP_MEMBER
)
db.add(top_member)
db.commit()
```

5. Run the server:
```bash
python main.py
```

6. Open http://localhost:8000 in your browser

## Deployment Options

### Option 1: Render (Recommended - Free & Easy)

1. Go to [Render.com](https://render.com) and sign up
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `PORT=8000`
7. Deploy!

### Option 2: Railway (Free Tier Available)

1. Go to [Railway.app](https://railway.app) and sign up
2. Create a new project
3. Connect your GitHub repository
4. Railway will auto-detect Python and deploy
5. Add environment variables if needed

### Option 3: Vercel (Requires Adjustment)

Vercel supports Python but requires serverless function setup:

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Follow the prompts
4. Note: You may need to adjust the code for serverless functions

### Option 4: PythonAnywhere (Free Tier)

1. Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)
2. Upload your files via the web interface
3. Create a web app and point it to your `main.py`
4. Configure static files mapping

### Option 5: Heroku (Free Tier Discontinued, but Paid Available)

1. Install Heroku CLI
2. Run `heroku create your-app-name`
3. Create `Procfile` with: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Run `git push heroku main`

## Environment Variables

Create a `.env` file or set environment variables:

```
SECRET_KEY=your-secret-key-here-change-in-production
```

## Database

The system uses SQLite by default. For production, consider upgrading to PostgreSQL:

1. Update `database.py`:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

2. Update `requirements.txt`:
```
psycopg2-binary==2.9.9
```

## API Endpoints

- `POST /api/auth/register` - Register new member
- `POST /api/auth/login` - Login (top members only)
- `GET /api/members` - List all members
- `GET /api/shares` - List all shares
- `POST /api/business-plans` - Create business plan
- `GET /api/business-plans` - List all business plans
- `POST /api/business-plans/{id}/vote` - Vote on business plan
- `POST /api/business-plans/{id}/profit` - Record profit
- `GET /api/members/{id}/statement` - Get member statement

## Business Logic

### Share System
- Base shares: ₹100 per share, monthly payment required
- Additional shares: ₹100 per share, one-time purchase
- Base shares can only be increased, not decreased

### Business Plan Voting
- 3-day voting period
- Majority vote required for approval
- Non-voters automatically get minimum share criteria applied

### Funding Rounds
- **Scenario 1**: All members vote yes → equal share distribution
- **Scenario 2**: Partial yes votes → Round 1 (yes voters), Round 2 (all members)

### Profit Distribution
- Proposer gets 10% bonus
- Remaining profit distributed based on share allocation
- Can book percentage or carry forward to additional shares

## Security Notes

- Only top members can login
- JWT token authentication
- Password hashing with bcrypt
- SQL injection protection via SQLAlchemy

## License

Private - For Fahran Business Use Only

