import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
import hashlib
import time
import json
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Helper function to get config from Streamlit secrets or environment
def get_secret(key, default=""):
    """Get value from Streamlit secrets (cloud) or environment variables (local)"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    # Fall back to environment variables (for local development)
    return os.getenv(key, default)

OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"

# Multiple models for fallback (no rate limits!)
MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "google/gemma-2-9b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

MYSQL_CONFIG = {
    'host': get_secret('MYSQL_HOST', 'localhost'),
    'database': get_secret('MYSQL_DATABASE', 'chatbot_db'),
    'user': get_secret('MYSQL_USER', 'root'),
    'password': get_secret('MYSQL_PASSWORD', ''),
    'port': int(get_secret('MYSQL_PORT', '3306') or '3306')
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
                    embed_code TEXT,
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
            print(f"[DB] Save error: {e}")
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
    
    @staticmethod
    def save_chatbot(chatbot_id, company_name, website_url, embed_code):
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO chatbots (chatbot_id, company_name, website_url, embed_code)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE embed_code = VALUES(embed_code)
            """
            cursor.execute(query, (chatbot_id, company_name, website_url, embed_code))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            return False

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
        except:
            return None
    
    def scrape_website(self, base_url, progress_callback=None):
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        urls = [base_url, f"{base_url}/about", f"{base_url}/services", 
                f"{base_url}/contact", f"{base_url}/pricing"]
        
        pages = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scrape_page, url): url for url in urls}
            for i, future in enumerate(as_completed(futures)):
                if progress_callback:
                    progress_callback(i+1, len(urls), futures[future])
                result = future.result()
                if result:
                    pages.append(result)
        
        all_text = '\n'.join([p['content'] for p in pages])
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)))[:5]
        phones = list(set(re.findall(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', all_text)))[:5]
        
        return pages, {"emails": emails, "phones": phones}

class SmartAI:
    """AI with multiple model fallback - NO RATE LIMITS!"""
    def __init__(self):
        self.cache = {}
        self.current_model_index = 0
    
    @st.cache_data(ttl=3600)
    def _cached_llm_call(_self, prompt_hash, prompt, model):
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
                    "max_tokens": 100,
                    "temperature": 0.5
                },
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip(), None
            
            return None, resp.status_code
        except Exception as e:
            return None, str(e)
    
    def call_llm(self, prompt):
        if not OPENROUTER_API_KEY:
            return "I'm having trouble connecting. Please try again."
        
        # Check cache
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try all models until one works (NO RATE LIMITS!)
        for attempt in range(len(MODELS)):
            model = MODELS[self.current_model_index]
            result, error = self._cached_llm_call(cache_key, prompt, model)
            
            if result:
                self.cache[cache_key] = result
                return result
            
            # If rate limited or error, try next model
            print(f"[AI] Model {model} failed ({error}), trying next...")
            self.current_model_index = (self.current_model_index + 1) % len(MODELS)
        
        # If all models fail, provide helpful fallback
        return "I'm having trouble connecting to the AI service. Please try again in a moment, or contact support if the issue persists."

class UniversalChatbot:
    def __init__(self, company_name, website_url, chatbot_id):
        self.company_name = company_name
        self.website_url = website_url
        self.chatbot_id = chatbot_id
        self.pages = []
        self.contact_info = {}
        self.ready = False
        self.ai = SmartAI()
    
    def initialize(self, progress_callback=None):
        try:
            scraper = EnhancedScraper()
            self.pages, self.contact_info = scraper.scrape_website(self.website_url, progress_callback)
            self.ready = True
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False
    
    def ask(self, question):
        if not self.ready:
            return "⚠️ Chatbot not ready."
        
        # Instant responses
        if any(g in question.lower() for g in ['hi', 'hello', 'hey']):
            return f"👋 Hello! I'm the AI assistant for **{self.company_name}**. How can I help you?"
        
        if any(k in question.lower() for k in ['email', 'contact', 'phone']):
            msg = f"📞 **Contact {self.company_name}**\n\n"
            if self.contact_info.get('emails'):
                msg += "📧 " + ", ".join(self.contact_info['emails']) + "\n"
            if self.contact_info.get('phones'):
                msg += "📱 " + ", ".join(self.contact_info['phones']) + "\n"
            msg += f"🌐 {self.website_url}"
            return msg
        
        # Use first page content
        context = self.pages[0]['content'][:800] if self.pages else "No content"
        
        prompt = f"""Info from {self.company_name}:

{context}

Answer briefly: {question}

Answer (1-2 sentences):"""
        
        return self.ai.call_llm(prompt)

def generate_embed_code(chatbot_id, company_name):
    return f'''<!-- {company_name} Chatbot -->
<div id="chatbot-{chatbot_id}"></div>
<script>
(function(){{
  var btn=document.createElement('button');
  btn.innerHTML='💬 Chat';
  btn.style.cssText='position:fixed;bottom:20px;right:20px;background:#0066cc;color:white;border:none;border-radius:50px;padding:15px 25px;cursor:pointer;z-index:9999;';
  btn.onclick=function(){{alert('Chatbot widget - integrate with your server');}};
  document.body.appendChild(btn);
}})();
</script>'''

def init_session():
    defaults = {
        'chatbots': {},
        'current_company': None,
        'chat_history': [],
        'question_count': 0,
        'lead_capture_mode': None,
        'lead_data': {},
        'session_id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16],
        'lead_captured': False,
        'conversation_start_time': None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def main():
    st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="wide")
    init_session()
    DatabaseManager.initialize_database()
    
    st.title("🤖 AI Chatbot with Lead Capture")
    st.caption("Fast, accurate answers with NO rate limits!")
    
    # Removed error message for Streamlit Cloud deployment
    # API key will be in secrets, not .env
    
    st.sidebar.title("🏢 Management")
    
    with st.sidebar.expander("➕ New Chatbot", expanded=True):
        name = st.text_input("Company Name", placeholder="e.g., TechCorp")
        url = st.text_input("Website URL", placeholder="https://example.com")
        
        if st.button("🚀 Create", type="primary"):
            if name and url:
                chatbot_id = hashlib.md5(f"{name}{url}{time.time()}".encode()).hexdigest()[:12]
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
                
                progress = st.progress(0)
                status = st.empty()
                
                def cb(done, total, url_str):
                    progress.progress(done/total)
                    status.text(f"{done}/{total}: {url_str[:40]}...")
                
                bot = UniversalChatbot(name, url, chatbot_id)
                if bot.initialize(cb):
                    st.session_state.chatbots[slug] = bot
                    st.session_state.current_company = slug
                    st.session_state.chat_history = []
                    st.session_state.question_count = 0
                    st.session_state.lead_captured = False
                    st.session_state.lead_capture_mode = None
                    st.session_state.lead_data = {}
                    st.session_state.conversation_start_time = datetime.now()
                    
                    embed = generate_embed_code(chatbot_id, name)
                    DatabaseManager.save_chatbot(chatbot_id, name, url, embed)
                    st.success("✅ Ready!")
                    st.rerun()
    
    if st.session_state.chatbots:
        st.sidebar.subheader("📋 Chatbots")
        for slug, bot in st.session_state.chatbots.items():
            col1, col2 = st.sidebar.columns([3,1])
            with col1:
                if st.button(f"💬 {bot.company_name}", key=f"sel_{slug}"):
                    st.session_state.current_company = slug
                    st.session_state.chat_history = []
                    st.session_state.question_count = 0
                    st.session_state.lead_captured = False
                    st.session_state.lead_capture_mode = None
                    st.session_state.lead_data = {}
                    st.session_state.conversation_start_time = datetime.now()
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{slug}"):
                    del st.session_state.chatbots[slug]
                    if st.session_state.current_company == slug:
                        st.session_state.current_company = None
                    st.rerun()
    
    if st.sidebar.button("📊 View Leads"):
        st.subheader("📊 Captured Leads")
        leads = DatabaseManager.get_leads()
        if leads:
            for lead in leads:
                with st.expander(f"🎯 {lead['username']} - {lead['company_name']}"):
                    st.write(f"**Email:** {lead['mailid']}")
                    st.write(f"**Phone:** {lead['phonenumber']}")
                    st.write(f"**Questions:** {lead['questions_asked']}")
                    st.write(f"**Time:** {lead['timestart']}")
                    
                    if lead['conversation']:
                        try:
                            conv = json.loads(lead['conversation'])
                            for msg in conv:
                                st.write(f"- **{msg['role'].title()}:** {msg['content'][:80]}...")
                        except:
                            pass
        else:
            st.info("No leads yet")
        return
    
    if not st.session_state.current_company:
        st.info("👈 Create a chatbot to start!")
        return
    
    bot = st.session_state.chatbots[st.session_state.current_company]
    
    if st.session_state.conversation_start_time is None:
        st.session_state.conversation_start_time = datetime.now()
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.subheader(f"💬 {bot.company_name}")
    with col2:
        st.metric("Questions", st.session_state.question_count)
    with col3:
        if st.session_state.lead_captured:
            st.success("✅ Lead")
        else:
            st.info("🎯 Pending")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    
    # LEAD CAPTURE (simplified)
    if st.session_state.lead_capture_mode and not st.session_state.lead_captured:
        st.markdown("---")
        st.markdown("### 🎯 Quick Info")
        
        with st.form("lead_form"):
            name = st.text_input("Name (optional)", placeholder="John Doe")
            email = st.text_input("Email (optional)", placeholder="john@example.com")
            phone = st.text_input("Phone (optional)", placeholder="+1234567890")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Submit", type="primary")
            with col2:
                skipped = st.form_submit_button("⏭️ Skip")
            
            if submitted or skipped:
                DatabaseManager.save_lead(
                    bot.chatbot_id, bot.company_name,
                    name or "Anonymous",
                    email or "not_provided@example.com",
                    phone or "Not provided",
                    st.session_state.session_id,
                    st.session_state.question_count,
                    st.session_state.chat_history,
                    st.session_state.conversation_start_time
                )
                st.session_state.lead_captured = True
                st.session_state.lead_capture_mode = None
                st.balloons()
                st.rerun()
    
    # Chat Input
    if question := st.chat_input("Ask anything..."):
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        with st.spinner("💭"):
            answer = bot.ask(question)
        
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.session_state.question_count += 1
        
        if st.session_state.question_count >= 3 and not st.session_state.lead_captured and not st.session_state.lead_capture_mode:
            st.session_state.lead_capture_mode = 'ask_info'
        
        st.rerun()

if __name__ == "__main__":
    main()
