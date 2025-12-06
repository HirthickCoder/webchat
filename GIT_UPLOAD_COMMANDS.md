# 🚀 GIT COMMANDS TO UPLOAD TO GITHUB

## Step-by-Step Commands

### 1. Navigate to Your Project Folder

```bash
cd C:\Users\Hirthick\.gemini\antigravity\scratch\chatbot_lead_generator
```

### 2. Initialize Git (if not already done)

```bash
git init
```

### 3. Add Remote Repository

```bash
git remote add origin https://github.com/ASWINKUMARD/chatbot.git
```

### 4. Create .gitignore File

```bash
echo .env > .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore
echo .streamlit/ >> .gitignore
```

### 5. Add All Files

```bash
git add .
```

### 6. Commit Files

```bash
git commit -m "Initial commit: AI Chatbot with Lead Capture"
```

### 7. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

---

## 📋 Complete Copy-Paste Script

**Copy and paste this entire block:**

```bash
cd C:\Users\Hirthick\.gemini\antigravity\scratch\chatbot_lead_generator

git init

git remote add origin https://github.com/ASWINKUMARD/chatbot.git

echo .env > .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore
echo .streamlit/ >> .gitignore

git add .

git commit -m "Initial commit: AI Chatbot with Lead Capture - Multi-model system with no rate limits"

git branch -M main

git push -u origin main
```

---

## ⚠️ If Repository Already Exists

If you get an error that the repository already has files:

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## 🔐 Authentication

When you run `git push`, you'll be asked for credentials:

**Option 1: Personal Access Token (Recommended)**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`
4. Copy the token
5. Use as password when prompted

**Option 2: GitHub Desktop**
- Download GitHub Desktop
- Sign in
- Open your folder
- Click "Publish repository"

---

## ✅ Files That Will Be Uploaded

- ✅ `app_final.py` (main application - NO RATE LIMITS)
- ✅ `requirements.txt`
- ✅ `database_setup.sql`
- ✅ `.env.example` (template)
- ✅ `README.md`
- ✅ `SETUP_INSTRUCTIONS.md`
- ✅ All other documentation files

**NOT uploaded:**
- ❌ `.env` (your secrets - protected by .gitignore)

---

## 🎯 Quick Verification

After pushing, check:

```bash
git status
```

Should show: "nothing to commit, working tree clean"

Visit: https://github.com/ASWINKUMARD/chatbot

You should see all your files! 🎉

---

## 🔄 Future Updates

When you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

---

## 💡 Pro Tips

1. **Never commit .env file** (contains secrets)
2. **Write clear commit messages**
3. **Push regularly** (backup your work)
4. **Use branches** for experiments

---

**Ready to upload? Run the commands above!** 🚀
