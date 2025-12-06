# 🚀 SETUP GUIDE - Send this to your friend

## Prerequisites
Your friend needs to install:
1. **Python 3.10+** - https://www.python.org/downloads/
2. **MySQL 8.0+** - https://dev.mysql.com/downloads/installer/
3. **Git** (optional) - https://git-scm.com/downloads

---

## STEP 1: Install MySQL Server

1. Download MySQL Installer: https://dev.mysql.com/downloads/installer/
2. Run the installer and choose "Developer Default"
3. During setup, set the **root password**: `Aswin@0099` (or choose your own)
4. Make sure MySQL Server is **running** (check Windows Services)

---

## STEP 2: Create Database

**Option A: Using MySQL Workbench (GUI)**
1. Open MySQL Workbench
2. Connect to localhost (username: `root`, password: `Aswin@0099`)
3. Open the file: `database_setup.sql`
4. Click the lightning bolt icon ⚡ to execute
5. You should see: "chatbot_db" database created with 2 tables

**Option B: Using Command Line**
```bash
# Login to MySQL
mysql -u root -p
# Enter password: Aswin@0099

# Create database
CREATE DATABASE chatbot_db;

# Use the database
USE chatbot_db;

# Copy and paste the entire SQL from database_setup.sql
# OR import the file:
source C:/path/to/database_setup.sql;

# Exit
exit;
```

---

## STEP 3: Get the Project Files

Copy the entire folder to your friend's laptop:
```
chatbot_lead_generator/
├── app.py
├── requirements.txt
├── database_setup.sql
├── .env.example
└── README.md
```

---

## STEP 4: Setup Environment Variables

1. Copy `.env.example` to `.env`
2. Edit `.env` file with your credentials:

```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_DATABASE=chatbot_db
MYSQL_USER=root
MYSQL_PASSWORD=Aswin@0099
MYSQL_PORT=3306

# OpenRouter API Configuration
OPENROUTER_API_KEY=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
```

---

## STEP 5: Install Python Dependencies

**Open PowerShell** in the project folder and run:

```powershell
# Create virtual environment
py -3.13 -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## STEP 6: Test Database Connection

```powershell
# Make sure venv is activated (you should see (venv) in prompt)
python test_db_connection.py
```

**Expected output:**
```
✅ Connected successfully!
✅ Found 2 table(s):
   - leads
   - chatbots
✅ All checks passed! Database is ready.
```

**If you see errors:**
- ❌ "Can't connect" → MySQL server is not running
- ❌ "Access denied" → Wrong password in .env file
- ❌ "Unknown database" → Run database_setup.sql first

---

## STEP 7: Run the Application

```powershell
# Make sure venv is activated
streamlit run app.py
```

**The app should open in your browser at:** http://localhost:8501

---

## ✅ VERIFICATION CHECKLIST

Before running the app, verify:

- [ ] MySQL Server is running (check Windows Services)
- [ ] Database `chatbot_db` exists (check in MySQL Workbench)
- [ ] Tables `leads` and `chatbots` exist
- [ ] `.env` file exists with correct credentials
- [ ] Virtual environment is activated (see `(venv)` in terminal)
- [ ] All packages installed successfully
- [ ] `test_db_connection.py` shows "✅ Connected successfully!"

---

## 🛠️ TROUBLESHOOTING

### Issue 1: MySQL Not Running
**Solution:**
1. Press `Win + R`
2. Type `services.msc`
3. Find "MySQL80" or "MySQL"
4. Right-click → Start

### Issue 2: Error 401 (API Key Invalid)
**Solution:**
- Go to https://openrouter.ai/
- Login and get a new API key
- Update `OPENROUTER_API_KEY` in `.env` file

### Issue 3: Virtual Environment Won't Activate
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 4: Database Connection Failed
**Solution:**
1. Check MySQL is running
2. Verify credentials in `.env` match MySQL password
3. Make sure port 3306 is not blocked by firewall

---

## 📝 QUICK COMMANDS REFERENCE

**Every time you want to run the app:**
```powershell
# Navigate to project folder
cd "C:\path\to\chatbot_lead_generator"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run app
streamlit run app.py
```

**To stop the app:**
Press `Ctrl + C` in the terminal

**To deactivate virtual environment:**
```powershell
deactivate
```

---

## 🎯 TESTING THE APP

Once running:

1. **Create a chatbot:**
   - Company Name: `Test Company`
   - Website URL: `https://example.com`
   - Click "Create"

2. **Test chat:**
   - Ask 3 questions
   - Lead capture form should appear
   - Fill in details and submit

3. **View leads:**
   - Click "View Leads" in sidebar
   - You should see your captured lead

4. **Check database:**
   - Open MySQL Workbench
   - Run: `SELECT * FROM leads;`
   - You should see your data with userid, username, mailid, phonenumber, conversation, timestart, timeend

---

## 📧 Support

If something doesn't work:
1. Check the error message carefully
2. Verify all checklist items above
3. Try the troubleshooting section
4. Check MySQL Workbench to confirm database exists

---

**Created on:** 2025-12-06
**Version:** 1.0
