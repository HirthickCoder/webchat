# 🚀 AI Chatbot Lead Generator - FOR YOUR FRIEND

## Super Easy Setup (3 Steps)

### 1️⃣ Install MySQL
- Download: https://dev.mysql.com/downloads/installer/
- Choose "Developer Default"
- Set root password: `Aswin@0099`
- Make sure it's running

### 2️⃣ Create Database
Open MySQL Workbench:
- Connect to localhost
- Open file: `database_setup.sql`
- Click the lightning bolt ⚡
- Database created!

### 3️⃣ Run Setup
Double-click: **`FIRST_TIME_SETUP.bat`**
- This installs everything
- Takes 2-3 minutes

## 🎯 Running the App

**Every time you want to use it:**
Double-click: **`RUN_APP.bat`**

Your browser will open at: http://localhost:8501

## 📝 Configuration

If you need to change settings, edit `.env` file:
- MySQL password
- API key
- Database name

## 🛠️ Troubleshooting

**"Can't connect to database"**
→ Start MySQL service (services.msc → MySQL80 → Start)

**"Error 401"**
→ Invalid API key, check `.env` file

**"Virtual env error"**
→ Run PowerShell as admin and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 More Help

- **Detailed guide:** Open `SETUP_INSTRUCTIONS.md`
- **Quick commands:** Open `QUICK_COMMANDS.txt`
- **Test database:** Run `test_db_connection.py`

## ✅ Files Included

- `app.py` - Main application
- `database_setup.sql` - Database schema
- `requirements.txt` - Python packages
- `.env.example` - Configuration template
- `FIRST_TIME_SETUP.bat` - ⭐ Run this first
- `RUN_APP.bat` - ⭐ Run this to start app
- `test_db_connection.py` - Test DB connection
- `SETUP_INSTRUCTIONS.md` - Detailed guide
- `QUICK_COMMANDS.txt` - Command reference

## 🎉 That's It!

1. Install MySQL ✅
2. Run `FIRST_TIME_SETUP.bat` ✅
3. Run `RUN_APP.bat` ✅
4. Open browser ✅
5. Start chatting! ✅

---

**Need help?** Check `SETUP_INSTRUCTIONS.md` for details.
