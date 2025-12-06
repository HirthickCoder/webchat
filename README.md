# 🤖 AI Chatbot with Lead Capture

**Fast, accurate chatbot with NO rate limits!** Built with Streamlit, OpenRouter AI, and MySQL.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

- ✅ **No Rate Limits** - Uses 4 AI models with auto-switching
- ✅ **Fast Responses** - 2-3 second answers
- ✅ **Smart Scraping** - Extracts comprehensive website content
- ✅ **Lead Capture** - Automatic after 3 questions
- ✅ **MySQL Storage** - Stores conversations and leads
- ✅ **Custom URLs** - Scrape specific pages
- ✅ **Embed Code** - Easy website integration

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ASWINKUMARD/chatbot.git
cd chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database

```bash
# Start MySQL server
# Then run:
mysql -u root -p < database_setup.sql
```

### 4. Configure Environment

Create `.env` file:

```env
OPENROUTER_API_KEY=your_key_here
MYSQL_HOST=localhost
MYSQL_DATABASE=chatbot_db
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_PORT=3306
```

Get free API key: https://openrouter.ai/keys

### 5. Run Application

```bash
streamlit run app_final.py
```

Visit: http://localhost:8501

---

## 📖 Usage

### Create Chatbot

1. Enter company name
2. Enter website URL
3. Click "Create"

### Ask Questions

- "What services do you offer?"
- "How much does it cost?"
- "Do you have pricing plans?"

### View Leads

Click "View Leads" in sidebar to see captured leads with:
- Name, email, phone
- Full conversation history
- Timestamps

---

## 🎯 How It Works

### Multi-Model System

Uses 4 different AI models:
1. `meta-llama/llama-3.2-3b-instruct:free`
2. `microsoft/phi-3-mini-128k-instruct:free`
3. `google/gemma-2-9b-it:free`
4. `nousresearch/hermes-3-llama-3.1-405b:free`

**When one hits rate limit → auto-switches to next!**

### Web Scraping

Extracts:
- Page titles & descriptions
- Headings (H1-H4)
- Paragraphs & lists
- Tables
- Contact info (emails, phones)

### Lead Capture

Automatically triggers after 3 questions:
- Collects name, email, phone
- Saves full conversation
- Stores in MySQL
- Continues chat seamlessly

---

## 📁 Project Structure

```
chatbot/
├── app_final.py              # Main application (USE THIS!)
├── requirements.txt           # Python dependencies
├── database_setup.sql         # Database schema
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── SETUP_INSTRUCTIONS.md     # Detailed setup guide
└── GIT_UPLOAD_COMMANDS.md    # Git commands reference
```

---

## 🔧 Configuration

### Speed Settings

Edit `app_final.py` line 362:

```python
"max_tokens": 100,  # Adjust for answer length
timeout=5,          # Adjust for speed
```

### Context Size

Edit `app_final.py` line 467:

```python
context = self.pages[0]['content'][:800]  # Adjust chars
```

---

## 📊 Database Schema

### Leads Table

| Field | Type | Description |
|-------|------|-------------|
| userid | INT | Auto-increment ID |
| username | VARCHAR(255) | Lead name |
| mailid | VARCHAR(255) | Email address |
| phonenumber | VARCHAR(100) | Phone number |
| conversation | TEXT | JSON chat history |
| timestart | TIMESTAMP | Start time |
| timeend | TIMESTAMP | End time |
| chatbot_id | VARCHAR(255) | Chatbot identifier |
| company_name | VARCHAR(255) | Company name |
| session_id | VARCHAR(255) | Session identifier |
| questions_asked | INT | Question count |

### Chatbots Table

| Field | Type | Description |
|-------|------|-------------|
| id | INT | Auto-increment ID |
| chatbot_id | VARCHAR(255) | Unique identifier |
| company_name | VARCHAR(255) | Company name |
| website_url | TEXT | Website URL |
| embed_code | TEXT | Embed code |
| created_at | TIMESTAMP | Creation time |

---

## 🎨 Features in Detail

### 1. No Rate Limits

- Uses 4 different AI models
- Auto-switches on rate limit
- ~80 requests/min capacity
- Virtually unlimited for normal use

### 2. Fast Responses

- 2-3 seconds for new questions
- 0.1 seconds for cached questions
- Instant for greetings/contact

### 3. Smart Caching

- Caches responses for 1 hour
- Instant for repeated questions
- Reduces API calls

### 4. Lead Capture

- Triggers after 3 questions
- One simple form
- Saves to MySQL
- Continues conversation

---

## 🚀 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Visit https://streamlit.io/cloud
3. Connect repository
4. Add secrets in dashboard
5. Deploy!

### Secrets Configuration

Add in Streamlit Cloud dashboard:

```toml
OPENROUTER_API_KEY = "your_key"
MYSQL_HOST = "your_host"
MYSQL_DATABASE = "chatbot_db"
MYSQL_USER = "your_user"
MYSQL_PASSWORD = "your_password"
MYSQL_PORT = "3306"
```

---

## 📝 Requirements

- Python 3.8+
- MySQL 8.0+
- OpenRouter API key (free)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

---

## 📄 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- OpenRouter for free AI API
- Streamlit for amazing framework
- BeautifulSoup for web scraping

---

## 📞 Support

- **Issues:** https://github.com/ASWINKUMARD/chatbot/issues
- **Email:** aswinkumardoffl@gmail.com

---

## 🎉 Star This Repo!

If you find this useful, please ⭐ star this repository!

---

**Built with ❤️ by ASWINKUMARD**

