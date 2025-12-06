from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import time
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "google/gemma-2-9b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'chatbot_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

class DatabaseManager:
    @staticmethod
    def create_connection():
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            return conn if conn.is_connected() else None
        except Error as e:
            print(f"[DB] Error: {e}")
            return None
    
    @staticmethod
    def initialize_database():
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    userid INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    mailid VARCHAR(255),
                    phonenumber VARCHAR(100),
                    conversation TEXT,
                    timestart TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    timeend TIMESTAMP NULL,
                    chatbot_id VARCHAR(255),
                    company_name VARCHAR(255),
                    session_id VARCHAR(255),
                    questions_asked INT DEFAULT 0,
                    INDEX idx_chatbot_id (chatbot_id),
                    INDEX idx_mailid (mailid),
                    INDEX idx_session_id (session_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chatbots (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    chatbot_id VARCHAR(255) UNIQUE NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    website_url TEXT NOT NULL,
                    scraped_content TEXT,
                    contact_info TEXT,
                    embed_code TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_chatbot_id (chatbot_id)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"[DB] Init error: {e}")
            return False
    
    @staticmethod
    def save_chatbot(chatbot_id, company_name, website_url, scraped_content, contact_info, embed_code):
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO chatbots (chatbot_id, company_name, website_url, scraped_content, contact_info, embed_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE scraped_content = VALUES(scraped_content), contact_info = VALUES(contact_info)
            """
            cursor.execute(query, (chatbot_id, company_name, website_url, 
                                 json.dumps(scraped_content), json.dumps(contact_info), embed_code))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"[DB] Save error: {e}")
            return False
    
    @staticmethod
    def get_chatbot(chatbot_id):
        conn = DatabaseManager.create_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM chatbots WHERE chatbot_id = %s", (chatbot_id,))
            chatbot = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if chatbot and chatbot['scraped_content']:
                chatbot['scraped_content'] = json.loads(chatbot['scraped_content'])
            if chatbot and chatbot['contact_info']:
                chatbot['contact_info'] = json.loads(chatbot['contact_info'])
            
            return chatbot
        except Error as e:
            print(f"[DB] Get error: {e}")
            return None
    
    @staticmethod
    def get_all_chatbots():
        conn = DatabaseManager.create_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM chatbots ORDER BY created_at DESC")
            chatbots = cursor.fetchall()
            cursor.close()
            conn.close()
            return chatbots
        except Error as e:
            return []
    
    @staticmethod
    def save_lead(chatbot_id, company_name, username, mailid, phonenumber, 
                  session_id, questions_asked, conversation, timestart):
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO leads 
                (chatbot_id, company_name, username, mailid, phonenumber, 
                 session_id, questions_asked, conversation, timestart)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            conv_json = json.dumps(conversation) if conversation else "[]"
            
            cursor.execute(query, (
                chatbot_id, company_name, 
                username or "Anonymous", 
                mailid or "not_provided@example.com", 
                phonenumber or "Not provided", 
                session_id, questions_asked, conv_json, timestart
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"[DB] Save lead error: {e}")
            return False
    
    @staticmethod
    def get_leads(chatbot_id=None):
        conn = DatabaseManager.create_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            if chatbot_id:
                cursor.execute("SELECT * FROM leads WHERE chatbot_id = %s ORDER BY timestart DESC", (chatbot_id,))
            else:
                cursor.execute("SELECT * FROM leads ORDER BY timestart DESC")
            leads = cursor.fetchall()
            cursor.close()
            conn.close()
            return leads
        except Error as e:
            return []

class EnhancedScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = 8
    
    def extract_content(self, soup):
        content_parts = []
        
        if soup.title:
            content_parts.append(f"TITLE: {soup.title.string}")
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content_parts.append(f"DESC: {meta_desc.get('content')}")
        
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for h in headings[:15]:
            text = h.get_text(strip=True)
            if text:
                content_parts.append(f"{h.name.upper()}: {text}")
        
        paragraphs = soup.find_all('p')
        for p in paragraphs[:20]:
            text = p.get_text(strip=True)
            if len(text) > 20:
                content_parts.append(text)
        
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists[:5]:
            items = lst.find_all('li')
            for item in items[:10]:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    content_parts.append(f"• {text}")
        
        return '\n'.join(content_parts)[:4000]
    
    def scrape_page(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
                tag.decompose()
            
            content = self.extract_content(soup)
            if not content or len(content) < 100:
                return None
            
            return {"url": url, "content": content}
        except Exception as e:
            print(f"Scrape error for {url}: {e}")
            return None
    
    def scrape_website(self, base_url):
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        urls = [base_url, f"{base_url}/about", f"{base_url}/services", 
                f"{base_url}/contact", f"{base_url}/pricing"]
        
        pages = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scrape_page, url): url for url in urls}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    pages.append(result)
        
        all_text = '\n'.join([p['content'] for p in pages])
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)))[:5]
        phones = list(set(re.findall(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', all_text)))[:5]
        
        return pages, {"emails": emails, "phones": phones}

class SmartAI:
    def __init__(self):
        self.cache = {}
        self.current_model_index = 0
    
    def call_llm(self, prompt):
        if not OPENROUTER_API_KEY:
            return "I'm having trouble connecting. Please configure the API key."
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        for attempt in range(len(MODELS)):
            model = MODELS[self.current_model_index]
            try:
                resp = requests.post(
                    OPENROUTER_API_BASE,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com",
                        "X-Title": "Chatbot"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.7
                    },
                    timeout=10
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        result = data["choices"][0]["message"]["content"].strip()
                        self.cache[cache_key] = result
                        return result
            except Exception as e:
                print(f"[AI] Model {model} failed: {e}")
            
            self.current_model_index = (self.current_model_index + 1) % len(MODELS)
        
        return "I'm having trouble connecting to the AI service. Please try again."

# Initialize database on startup
DatabaseManager.initialize_database()
ai_engine = SmartAI()

# API Endpoints
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🤖 Chatbot API - Successfully Deployed!",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "chatbots": {
                "list": "GET /api/chatbots",
                "get": "GET /api/chatbot/<chatbot_id>",
                "create": "POST /api/chatbot/create"
            },
            "chat": "POST /api/chat",
            "leads": {
                "capture": "POST /api/lead/capture",
                "list": "GET /api/leads",
                "stats": "GET /api/stats"
            }
        },
        "documentation": "https://github.com/ASWINKUMARD/chatbot"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/chatbots', methods=['GET'])
def get_chatbots():
    chatbots = DatabaseManager.get_all_chatbots()
    return jsonify({"success": True, "chatbots": chatbots})

@app.route('/api/chatbot/<chatbot_id>', methods=['GET'])
def get_chatbot(chatbot_id):
    chatbot = DatabaseManager.get_chatbot(chatbot_id)
    if chatbot:
        return jsonify({"success": True, "chatbot": chatbot})
    return jsonify({"success": False, "error": "Chatbot not found"}), 404

@app.route('/api/chatbot/create', methods=['POST'])
def create_chatbot():
    data = request.json
    company_name = data.get('company_name')
    website_url = data.get('website_url')
    
    if not company_name or not website_url:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    try:
        chatbot_id = hashlib.md5(f"{company_name}{website_url}{time.time()}".encode()).hexdigest()[:12]
        
        scraper = EnhancedScraper()
        pages, contact_info = scraper.scrape_website(website_url)
        
        if not pages:
            return jsonify({"success": False, "error": "Failed to scrape website"}), 400
        
        embed_code = f'''<!-- {company_name} Chatbot -->
<script src="https://yourdomain.com/chatbot.js" data-chatbot-id="{chatbot_id}"></script>'''
        
        success = DatabaseManager.save_chatbot(
            chatbot_id, company_name, website_url, pages, contact_info, embed_code
        )
        
        if success:
            return jsonify({
                "success": True,
                "chatbot_id": chatbot_id,
                "company_name": company_name,
                "embed_code": embed_code
            })
        else:
            return jsonify({"success": False, "error": "Database error"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    chatbot_id = data.get('chatbot_id')
    message = data.get('message')
    
    if not chatbot_id or not message:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    chatbot = DatabaseManager.get_chatbot(chatbot_id)
    if not chatbot:
        return jsonify({"success": False, "error": "Chatbot not found"}), 404
    
    # Handle greetings
    if any(g in message.lower() for g in ['hi', 'hello', 'hey']):
        response = f"👋 Hello! I'm the AI assistant for **{chatbot['company_name']}**. How can I help you today?"
        return jsonify({"success": True, "response": response})
    
    # Handle contact requests
    if any(k in message.lower() for k in ['email', 'contact', 'phone']):
        contact_info = chatbot.get('contact_info', {})
        response = f"📞 **Contact {chatbot['company_name']}**\n\n"
        if contact_info.get('emails'):
            response += "📧 " + ", ".join(contact_info['emails']) + "\n"
        if contact_info.get('phones'):
            response += "📱 " + ", ".join(contact_info['phones']) + "\n"
        response += f"🌐 {chatbot['website_url']}"
        return jsonify({"success": True, "response": response})
    
    # Use AI for other queries
    scraped_content = chatbot.get('scraped_content', [])
    context = scraped_content[0]['content'][:800] if scraped_content else "No content available"
    
    prompt = f"""You are a helpful AI assistant for {chatbot['company_name']}.

Company Information:
{context}

User Question: {message}

Provide a helpful, concise answer (2-3 sentences):"""
    
    response = ai_engine.call_llm(prompt)
    return jsonify({"success": True, "response": response})

@app.route('/api/lead/capture', methods=['POST'])
def capture_lead():
    data = request.json
    
    required_fields = ['chatbot_id', 'company_name', 'session_id', 'conversation']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    success = DatabaseManager.save_lead(
        data['chatbot_id'],
        data['company_name'],
        data.get('username', 'Anonymous'),
        data.get('email', 'not_provided@example.com'),
        data.get('phone', 'Not provided'),
        data['session_id'],
        data.get('questions_asked', 0),
        data['conversation'],
        data.get('timestart', datetime.now())
    )
    
    if success:
        return jsonify({"success": True, "message": "Lead captured successfully"})
    return jsonify({"success": False, "error": "Database error"}), 500

@app.route('/api/leads', methods=['GET'])
def get_leads():
    chatbot_id = request.args.get('chatbot_id')
    leads = DatabaseManager.get_leads(chatbot_id)
    return jsonify({"success": True, "leads": leads})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    chatbot_id = request.args.get('chatbot_id')
    leads = DatabaseManager.get_leads(chatbot_id)
    
    total_leads = len(leads)
    total_questions = sum(lead.get('questions_asked', 0) for lead in leads)
    avg_questions = total_questions / total_leads if total_leads > 0 else 0
    
    stats = {
        "total_leads": total_leads,
        "total_questions": total_questions,
        "avg_questions": round(avg_questions, 2),
        "conversion_rate": 0  # Calculate based on your metrics
    }
    
    return jsonify({"success": True, "stats": stats})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
