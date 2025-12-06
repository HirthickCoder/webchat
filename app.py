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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv not installed, will use system environment variables

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "kwaipilot/kat-coder-pro:free"

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'chatbot_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'port': int(os.getenv('MYSQL_PORT', '3306')) if os.getenv('MYSQL_PORT', '').strip() else 3306
}

class DatabaseManager:
    @staticmethod
    def create_connection():
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            return conn if conn.is_connected() else None
        except Error as e:
            print(f"[DB] Error: {e}")
            st.error(f"Database connection error: {e}")
            return None
    
    @staticmethod
    def initialize_database():
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Create leads table with requested schema
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
            
            # Create chatbots table
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
            print("[DB] ✅ Database initialized")
            return True
        except Error as e:
            print(f"[DB] Init error: {e}")
            st.error(f"Database initialization error: {e}")
            return False
    
    @staticmethod
    def save_lead(chatbot_id, company_name, username, mailid, phonenumber, 
                  session_id, questions_asked, conversation, timestart):
        """Save lead with new schema: userid, username, mailid, phonenumber, conversation, timestart, timeend"""
        conn = DatabaseManager.create_connection()
        if not conn:
            print("[DB] ❌ Failed to connect to database")
            return False
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO leads 
                (chatbot_id, company_name, username, mailid, phonenumber, 
                 session_id, questions_asked, conversation, timestart)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Convert conversation to JSON string
            conv_json = json.dumps(conversation) if conversation else "[]"
            
            cursor.execute(query, (
                chatbot_id, 
                company_name, 
                username or "Anonymous", 
                mailid or "not_provided@example.com", 
                phonenumber or "Not provided", 
                session_id, 
                questions_asked, 
                conv_json,
                timestart
            ))
            
            conn.commit()
            userid = cursor.lastrowid
            cursor.close()
            conn.close()
            print(f"[DB] ✅ Lead saved with userid: {userid}")
            return True
        except Error as e:
            print(f"[DB] ❌ Save error: {e}")
            st.error(f"Failed to save lead: {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            return False
    
    @staticmethod
    def update_lead_endtime(session_id):
        """Update the timeend for a lead when conversation ends"""
        conn = DatabaseManager.create_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = """
                UPDATE leads 
                SET timeend = %s 
                WHERE session_id = %s AND timeend IS NULL
            """
            cursor.execute(query, (datetime.now(), session_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"[DB] Update error: {e}")
            return False
    
    @staticmethod
    def get_leads(chatbot_id=None):
        conn = DatabaseManager.create_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            if chatbot_id:
                cursor.execute(
                    "SELECT * FROM leads WHERE chatbot_id = %s ORDER BY timestart DESC", 
                    (chatbot_id,)
                )
            else:
                cursor.execute("SELECT * FROM leads ORDER BY timestart DESC")
            leads = cursor.fetchall()
            cursor.close()
            conn.close()
            return leads
        except Error as e:
            print(f"[DB] Get error: {e}")
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
            print(f"[DB] Chatbot save error: {e}")
            return False

class FastScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.timeout = 6
    
    def scrape_page(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            
            content = soup.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 25][:50]
            
            return {"url": url, "content": '\n'.join(lines)[:4000]} if lines else None
        except:
            return None
    
    def scrape_website(self, base_url, progress_callback=None):
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        urls = [base_url, f"{base_url}/about", f"{base_url}/services", 
                f"{base_url}/contact", f"{base_url}/products"]
        
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
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)))[:3]
        phones = list(set(re.findall(r'\+?\d[\d\s.-]{7,}\d', all_text)))[:3]
        
        return pages, {"emails": emails, "phones": phones}

class SmartAI:
    def __init__(self):
        self.cache = {}
    
    def call_llm(self, prompt):
        if not OPENROUTER_API_KEY:
            return "⚠️ API key not set"
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            resp = requests.post(
                OPENROUTER_API_BASE,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data:
                    answer = data["choices"][0]["message"]["content"].strip()
                    self.cache[cache_key] = answer
                    return answer
            return f"⚠️ Error {resp.status_code}"
        except:
            return "I'm having connection issues. Please try again."

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
            scraper = FastScraper()
            self.pages, self.contact_info = scraper.scrape_website(self.website_url, progress_callback)
            self.ready = True
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False
    
    def ask(self, question):
        if not self.ready:
            return "⚠️ Not ready"
        
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
        
        context = '\n'.join([p['content'][:800] for p in self.pages[:3]])
        
        prompt = f"""You are a helpful assistant for {self.company_name}.

Context from their website:
{context}

User question: {question}

Provide a helpful, natural 2-3 sentence answer.

Answer:"""
        
        return self.ai.call_llm(prompt)

def generate_embed_code(chatbot_id, company_name):
    return f'''<!-- {company_name} AI Chatbot -->
<div id="chatbot-{chatbot_id}"></div>
<script>
(function(){{
  var btn=document.createElement('button');
  btn.innerHTML='💬 Chat';
  btn.style.cssText='position:fixed;bottom:20px;right:20px;background:#0066cc;color:white;border:none;border-radius:50px;padding:15px 25px;font-size:16px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);z-index:9999;';
  
  var iframe=document.createElement('iframe');
  iframe.src='YOUR_SERVER_URL?id={chatbot_id}';
  iframe.style.cssText='position:fixed;bottom:80px;right:20px;width:400px;height:600px;border:none;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.4);z-index:9998;display:none;';
  
  btn.onclick=function(){{
    iframe.style.display=iframe.style.display==='none'?'block':'none';
  }};
  
  document.body.appendChild(btn);
  document.body.appendChild(iframe);
}})();
</script>'''

def validate_email(email):
    """Validate email format - Basic check only"""
    if not email or not email.strip():
        return False
    return '@' in email and '.' in email.split('@')[-1]

def validate_phone(phone):
    """NO VALIDATION - Accept ANY phone number format"""
    if not phone or not phone.strip():
        return False
    return True

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
    st.set_page_config(page_title="AI Chatbot Lead Generator", page_icon="🤖", layout="wide")
    init_session()
    DatabaseManager.initialize_database()
    
    st.title("🤖 Universal AI Chatbot with Lead Capture")
    st.caption("Automatic lead capture after 3 questions + One-click website embed!")
    
    if not OPENROUTER_API_KEY:
        st.error("⚠️ OPENROUTER_API_KEY not set!")
        st.code("export OPENROUTER_API_KEY='your_key'")
        return
    
    st.sidebar.title("🏢 Management")
    
    with st.sidebar.expander("➕ New Chatbot", expanded=True):
        name = st.text_input("Company Name")
        url = st.text_input("Website URL")
        
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
                    st.write(f"**User ID:** {lead['userid']}")
                    st.write(f"**Email:** {lead['mailid']}")
                    st.write(f"**Phone:** {lead['phonenumber']}")
                    st.write(f"**Questions:** {lead['questions_asked']}")
                    st.write(f"**Start Time:** {lead['timestart']}")
                    st.write(f"**End Time:** {lead['timeend'] or 'In progress'}")
                    
                    # Calculate duration if both times exist
                    if lead['timeend']:
                        duration = lead['timeend'] - lead['timestart']
                        st.write(f"**Duration:** {duration}")
                    
                    # Show conversation
                    if lead['conversation']:
                        st.write("**Conversation:**")
                        try:
                            conv = json.loads(lead['conversation'])
                            for msg in conv:
                                st.write(f"- **{msg['role'].title()}:** {msg['content'][:100]}...")
                        except:
                            st.write(lead['conversation'][:200])
        else:
            st.info("No leads yet")
        return
    
    if not st.session_state.current_company:
        st.info("👈 Create a chatbot to start!")
        return
    
    bot = st.session_state.chatbots[st.session_state.current_company]
    
    # Initialize conversation start time if not set
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
    
    with st.expander("🔗 Get Embed Code", expanded=False):
        embed = generate_embed_code(bot.chatbot_id, bot.company_name)
        st.code(embed, language='html')
        st.download_button("📥 Download Widget", embed, f"{bot.company_name}_chatbot_widget.html", "text/html")
        st.info("Replace YOUR_SERVER_URL with your actual server URL")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    
    # LEAD CAPTURE FORM
    if st.session_state.lead_capture_mode and not st.session_state.lead_captured:
        st.markdown("---")
        st.markdown("### 🎯 We'd love to help you better!")
        
        if st.session_state.lead_capture_mode == 'ask_name':
            st.info("**May I know your name?**")
            name = st.text_input("Your Name", key="name_input", placeholder="e.g., John Doe")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Submit", type="primary", key="submit_name"):
                    if name and name.strip():
                        st.session_state.lead_data['name'] = name.strip()
                        st.session_state.lead_capture_mode = 'ask_email'
                        st.rerun()
                    else:
                        st.error("Please enter your name")
            with col2:
                if st.button("⏭️ Skip", key="skip_name"):
                    st.session_state.lead_data['name'] = "Anonymous"
                    st.session_state.lead_capture_mode = 'ask_email'
                    st.rerun()
        
        elif st.session_state.lead_capture_mode == 'ask_email':
            st.info("**What's your email address?**")
            email = st.text_input("Your Email", key="email_input", placeholder="e.g., john@example.com")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Submit", type="primary", key="submit_email"):
                    if email and validate_email(email):
                        st.session_state.lead_data['email'] = email.strip()
                        st.session_state.lead_capture_mode = 'ask_phone'
                        st.rerun()
                    else:
                        st.error("Please enter a valid email")
            with col2:
                if st.button("⏭️ Skip", key="skip_email"):
                    st.session_state.lead_data['email'] = "not_provided@example.com"
                    st.session_state.lead_capture_mode = 'ask_phone'
                    st.rerun()
        
        elif st.session_state.lead_capture_mode == 'ask_phone':
            st.info("**And your phone number?**")
            st.caption("Any format accepted - enter your number")
            phone = st.text_input("Your Phone", key="phone_input", 
                                placeholder="e.g., +1234567890, 123-456-7890, or any format")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Submit", type="primary", key="submit_phone"):
                    phone_value = phone.strip() if phone else "Not provided"
                    st.session_state.lead_data['phone'] = phone_value
                    
                    # Save to database with new schema
                    print(f"[DEBUG] Saving lead data: {st.session_state.lead_data}")
                    
                    with st.spinner("Saving..."):
                        success = DatabaseManager.save_lead(
                            bot.chatbot_id,
                            bot.company_name,
                            st.session_state.lead_data.get('name', 'Anonymous'),
                            st.session_state.lead_data.get('email', 'not_provided@example.com'),
                            st.session_state.lead_data.get('phone', 'Not provided'),
                            st.session_state.session_id,
                            st.session_state.question_count,
                            st.session_state.chat_history,
                            st.session_state.conversation_start_time
                        )
                    
                    if success:
                        st.session_state.lead_captured = True
                        st.session_state.lead_capture_mode = None
                        st.balloons()
                        st.success("✅ Thank you! Continuing chat...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Database save failed. Check console for details.")
            
            with col2:
                if st.button("⏭️ Skip", key="skip_phone"):
                    st.session_state.lead_data['phone'] = "Not provided"
                    
                    with st.spinner("Saving..."):
                        success = DatabaseManager.save_lead(
                            bot.chatbot_id,
                            bot.company_name,
                            st.session_state.lead_data.get('name', 'Anonymous'),
                            st.session_state.lead_data.get('email', 'not_provided@example.com'),
                            "Not provided",
                            st.session_state.session_id,
                            st.session_state.question_count,
                            st.session_state.chat_history,
                            st.session_state.conversation_start_time
                        )
                    
                    if success:
                        st.session_state.lead_captured = True
                        st.session_state.lead_capture_mode = None
                        st.balloons()
                        st.success("✅ Thank you! Continuing chat...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Database save failed. Check console for details.")
    
    # Chat Input
    if question := st.chat_input("Ask anything...", 
                                  disabled=bool(st.session_state.lead_capture_mode and not st.session_state.lead_captured)):
        if st.session_state.lead_capture_mode and not st.session_state.lead_captured:
            st.warning("⚠️ Please complete the form above")
        else:
            st.session_state.chat_history.append({"role": "user", "content": question})
            
            with st.spinner("Thinking..."):
                answer = bot.ask(question)
            
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.session_state.question_count += 1
            
            if st.session_state.question_count >= 3 and not st.session_state.lead_captured and not st.session_state.lead_capture_mode:
                st.session_state.lead_capture_mode = 'ask_name'
            
            st.rerun()

if __name__ == "__main__":
    main()
