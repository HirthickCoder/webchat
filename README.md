# 🤖 AI Chatbot Lead Generator

An intelligent chatbot application powered by AI that captures leads, scrapes website content, and provides automated customer support.

## ✨ Features

- 🚀 **AI-Powered Responses** - Uses advanced AI models for intelligent conversations
- 🌐 **Web Scraping** - Automatically learns from your website content
- 📊 **Lead Capture** - Stores customer information in MySQL database
- 💬 **Real-time Chat** - Beautiful, responsive chat interface
- 🔌 **REST API** - Full-featured API for integration

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **AI:** OpenRouter API / Google Gemini
- **Deployment:** Render (Backend) + Netlify (Frontend)

## 📋 Prerequisites

- Python 3.7+
- MySQL Server
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/chatbot-lead-generator.git
cd chatbot-lead-generator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env.local` file:

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=chatbot_db
MYSQL_PORT=3306

GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_key (optional)

FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Initialize Database

```bash
python -c "from app import DatabaseManager; DatabaseManager.initialize_database()"
```

### 5. Run the Application

```bash
python app.py
```

Or use the batch file:
```bash
RUN_FLASK.bat
```

The server will start at: http://localhost:5000

### 6. Open Chat Interface

Open `chat_interface.html` in your browser or navigate to `index.html`.

## 🌐 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions on deploying to:
- **Render** (Backend)
- **Netlify** (Frontend)
- **Railway/PlanetScale** (Database)

## 📁 Project Structure

```
chatbot/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── index.html               # Landing page
├── chat_interface.html      # Chat interface
├── test_db_connection.py    # Database connection tester
├── render.yaml              # Render deployment config
├── Procfile                 # Process configuration
├── netlify.toml             # Netlify configuration
├── DEPLOYMENT_GUIDE.md      # Deployment instructions
└── .env.local               # Environment variables (not in Git)
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/api/health` | GET | Health check |
| `/api/chatbot/create` | POST | Create new chatbot |
| `/api/chatbot/<id>` | GET | Get chatbot details |
| `/api/chat` | POST | Send chat message |
| `/api/lead/capture` | POST | Capture lead |
| `/api/leads` | GET | Get all leads |
| `/api/stats` | GET | Get statistics |

## 🧪 Testing

Test database connection:
```bash
python test_db_connection.py
```

Test API:
```bash
curl http://localhost:5000/api/health
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MYSQL_HOST` | MySQL server host | Yes |
| `MYSQL_USER` | MySQL username | Yes |
| `MYSQL_PASSWORD` | MySQL password | Yes |
| `MYSQL_DATABASE` | Database name | Yes |
| `MYSQL_PORT` | MySQL port (default: 3306) | No |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key | No |
| `FLASK_ENV` | Environment (development/production) | No |
| `FLASK_DEBUG` | Debug mode (True/False) | No |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Flask framework
- OpenRouter AI
- Google Gemini
- Beautiful Soup for web scraping

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ using Flask and AI
