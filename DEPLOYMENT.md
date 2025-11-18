# Deployment Guide - Fahran Business System

## Quick Start (Local Development)

1. **Run the startup script:**
```bash
./start.sh
```

2. **Or manually:**
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from database import init_db; init_db()"

# Create admin account
python3 setup_admin.py

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Open browser:** http://localhost:8000

---

## Free Hosting Options (Recommended Order)

### 🥇 Option 1: Render.com (EASIEST & FREE)

**Why Render?** Free tier, automatic deployments, easy setup, supports Python perfectly.

**Steps:**

1. **Sign up:** Go to https://render.com and create account (free)

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository (or push code to GitHub first)

3. **Configure:**
   - **Name:** fahran-business (or any name)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or paid if you want)

4. **Environment Variables:**
   - Add: `SECRET_KEY` = (generate a random string)

5. **Deploy:** Click "Create Web Service"

6. **Your site will be live at:** `https://your-app-name.onrender.com`

**Note:** Free tier sleeps after 15 min inactivity, but wakes up on first request.

---

### 🥈 Option 2: Railway.app (FREE TIER)

**Why Railway?** Very easy, good free tier, auto-detects Python.

**Steps:**

1. **Sign up:** https://railway.app (use GitHub login)

2. **New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Railway auto-detects:**
   - Automatically detects Python
   - Sets up build and start commands
   - You might need to adjust start command to: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variable:**
   - `SECRET_KEY` = (random string)

5. **Deploy:** Railway automatically deploys

6. **Your site:** `https://your-app-name.up.railway.app`

---

### 🥉 Option 3: PythonAnywhere (FREE)

**Why PythonAnywhere?** Free tier available, good for Python apps.

**Steps:**

1. **Sign up:** https://www.pythonanywhere.com (free account)

2. **Upload Files:**
   - Go to "Files" tab
   - Upload all your project files
   - Or use Git: `git clone https://github.com/your-repo.git`

3. **Create Web App:**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration" → Python 3.9
   - Set source code directory

4. **Configure WSGI:**
   - Edit WSGI file:
   ```python
   import sys
   path = '/home/yourusername/yourproject'
   if path not in sys.path:
       sys.path.append(path)
   
   from main import app
   application = app
   ```

5. **Static Files:**
   - Map `/static/` to `/home/yourusername/yourproject/static/`

6. **Reload:** Click "Reload" button

---

### Option 4: Vercel (Requires Serverless Setup)

**Note:** Vercel is better for frontend, but can work with Python serverless functions.

**Steps:**

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Follow prompts**

**Note:** You may need to adjust code for serverless functions. The `vercel.json` is included but might need tweaking.

---

## Database Setup for Production

### Using SQLite (Default - Works Fine)
- No setup needed, database file is created automatically
- Good for small to medium scale

### Using PostgreSQL (Recommended for Production)

1. **Get free PostgreSQL:**
   - Render: Free PostgreSQL database
   - Railway: Add PostgreSQL service
   - ElephantSQL: Free tier available

2. **Update `database.py`:**
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"
   ```

3. **Update `requirements.txt`:**
   ```
   psycopg2-binary==2.9.9
   ```

---

## First Time Setup After Deployment

1. **Create Admin Account:**
   - Use the API endpoint: `POST /api/auth/register`
   - Then manually set `is_top_member=True` in database
   - Or use the setup script locally and export database

2. **Or use Python console on server:**
   ```python
   from database import SessionLocal, Member, MemberType
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   db = SessionLocal()
   
   admin = Member(
       name="Admin",
       email="admin@example.com",
       password_hash=pwd_context.hash("your_password"),
       location="mumbai",
       is_top_member=True,
       member_type=MemberType.TOP_MEMBER
   )
   db.add(admin)
   db.commit()
   ```

---

## Environment Variables

Set these in your hosting platform:

- `SECRET_KEY`: Random string for JWT tokens (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `PORT`: Usually auto-set by hosting platform

---

## Troubleshooting

### Database Issues
- Make sure database file has write permissions
- For SQLite, ensure directory exists

### Static Files Not Loading
- Check static file path mapping
- Ensure `static/` directory is uploaded

### Authentication Not Working
- Verify `SECRET_KEY` is set
- Check JWT token expiration

### Port Issues
- Use `$PORT` environment variable (hosting platforms set this)
- Default to 8000 for local development

---

## Recommended: Render.com

**Why Render is best for this project:**
- ✅ Free tier available
- ✅ Perfect Python support
- ✅ Automatic HTTPS
- ✅ Easy environment variables
- ✅ GitHub integration
- ✅ Simple deployment
- ✅ Good documentation

**Free Tier Limits:**
- 750 hours/month (enough for always-on)
- Sleeps after 15 min inactivity (wakes on request)
- 512MB RAM
- Perfect for this application!

---

## Need Help?

1. Check logs in your hosting platform dashboard
2. Test locally first: `./start.sh`
3. Verify all files are uploaded
4. Check environment variables are set
5. Ensure database is initialized

---

**Quick Deploy Command (Render):**
Just push to GitHub and connect to Render - it's that easy! 🚀

