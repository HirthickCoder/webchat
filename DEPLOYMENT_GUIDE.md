# 🚀 Deployment Guide: Flask Chatbot to Cloud

## Quick Overview

Your chatbot application uses a **hybrid deployment strategy**:
- **Backend (Flask API):** Render.com
- **Frontend (HTML):** Netlify
- **Database:** Cloud MySQL (Railway/PlanetScale)

> [!IMPORTANT]
> Netlify **cannot** host Flask applications. It only supports static HTML/CSS/JS files.

---

## 📋 Prerequisites

Before deploying, you need:

1. ✅ GitHub account
2. ✅ Render account (free): https://render.com
3. ✅ Netlify account (free): https://netlify.com
4. ✅ Cloud MySQL database (Railway/PlanetScale)
5. ✅ Git installed on your computer

---

## Part 1: Setup Cloud MySQL Database

### Option A: Railway (Recommended)

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Provision MySQL"
4. Copy the connection details:
   - `MYSQL_HOST`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DATABASE`
   - `MYSQL_PORT`

### Option B: PlanetScale

1. Go to https://planetscale.com
2. Create a free database
3. Get connection credentials

---

## Part 2: Deploy Backend to Render

### Step 1: Push Code to GitHub

```bash
cd C:\Users\Hirthick\.gemini\antigravity\scratch\chatbot

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Flask chatbot"

# Create GitHub repo and push
# (Follow GitHub instructions to create repo and push)
```

### Step 2: Deploy on Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** `chatbot-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

### Step 3: Add Environment Variables

In Render dashboard, add these environment variables:

```
FLASK_ENV=production
FLASK_DEBUG=False
MYSQL_HOST=<your-railway-host>
MYSQL_USER=<your-railway-user>
MYSQL_PASSWORD=<your-railway-password>
MYSQL_DATABASE=chatbot_db
MYSQL_PORT=3306
GEMINI_API_KEY=AIzaSyBzyc_fYj8dy7BW-gEN497pvm5P60XfjHU
OPENROUTER_API_KEY=<optional>
```

### Step 4: Deploy

Click "Create Web Service" and wait for deployment (2-5 minutes).

Your API will be available at: `https://your-app-name.onrender.com`

---

## Part 3: Update Frontend API URL

### Update chat_interface.html

Open `chat_interface.html` and update line 303:

```javascript
// Change this line:
const API_BASE_URL = 'https://chatbot-kagh.onrender.com';

// To your new Render URL:
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

---

## Part 4: Deploy Frontend to Netlify

### Method 1: Drag & Drop (Easiest)

1. Go to https://app.netlify.com
2. Click "Add new site" → "Deploy manually"
3. Drag these files into the upload area:
   - `index.html`
   - `chat_interface.html`

Done! Your site will be live at: `https://random-name.netlify.app`

### Method 2: GitHub (Automatic Updates)

1. Push your code to GitHub (if not already done)
2. Go to Netlify → "Add new site" → "Import from Git"
3. Select your repository
4. Configure:
   - **Build command:** (leave empty)
   - **Publish directory:** `.`
5. Click "Deploy site"

---

## Part 5: Initialize Database Tables

After deploying to Render, initialize the database:

1. Go to your Render dashboard
2. Click on your web service
3. Go to "Shell" tab
4. Run:
   ```bash
   python -c "from app import DatabaseManager; DatabaseManager.initialize_database()"
   ```

---

## 🎉 Testing Your Deployment

### Test Backend API

```bash
curl https://your-app-name.onrender.com/api/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-12-07T..."}
```

### Test Frontend

1. Open your Netlify URL: `https://your-site.netlify.app`
2. Create a chatbot with company details
3. Start chatting!

---

## ⚠️ Important Notes

### Render Free Tier Limitations

> [!WARNING]
> Render free tier spins down after 15 minutes of inactivity. First request after spin-down takes **50+ seconds**.

### Database Connection

- Your local MySQL database (`localhost`) won't work in production
- You **must** use a cloud database (Railway/PlanetScale)
- Update environment variables in Render with cloud database credentials

### CORS Issues

The Flask app already has CORS enabled (`flask-cors`), so your Netlify frontend can communicate with Render backend.

---

## 🔧 Troubleshooting

### Backend not responding
- Check Render logs for errors
- Verify environment variables are set correctly
- Ensure database is accessible

### Frontend can't connect to backend
- Verify API_BASE_URL in `chat_interface.html`
- Check browser console for CORS errors
- Test backend API directly with curl

### Database connection errors
- Verify cloud database is running
- Check database credentials in Render
- Ensure database accepts connections from Render's IP

---

## 📁 Files Created for Deployment

- ✅ [render.yaml](file:///C:/Users/Hirthick/.gemini/antigravity/scratch/chatbot/render.yaml) - Render configuration
- ✅ [Procfile](file:///C:/Users/Hirthick/.gemini/antigravity/scratch/chatbot/Procfile) - Process configuration
- ✅ [netlify.toml](file:///C:/Users/Hirthick/.gemini/antigravity/scratch/chatbot/netlify.toml) - Netlify configuration
- ✅ [index.html](file:///C:/Users/Hirthick/.gemini/antigravity/scratch/chatbot/index.html) - Landing page
- ✅ [requirements.txt](file:///C:/Users/Hirthick/.gemini/antigravity/scratch/chatbot/requirements.txt) - Python dependencies (with gunicorn)

---

## 🎯 Next Steps

1. Set up cloud MySQL database (Railway recommended)
2. Push code to GitHub
3. Deploy backend to Render
4. Update `chat_interface.html` with your Render URL
5. Deploy frontend to Netlify
6. Test end-to-end functionality

Need help? Check the Render and Netlify documentation or reach out for support!
