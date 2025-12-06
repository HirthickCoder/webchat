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
MODEL = "meta-llama/llama-3.2-3b-instruct:free"  # Verified working model

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
        """Save lead with schema: userid, username, mailid, phonenumber, conversation, timestart, timeend"""
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

class EnhancedScraper:
    """Enhanced web scraper with comprehensive content extraction"""
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.timeout = 8
    
    def extract_comprehensive_content(self, soup):
        """Extract comprehensive structured content from page"""
        content_parts = []
        
        # Extract page title
        if soup.title:
            content_parts.append(f"PAGE TITLE: {soup.title.string}")
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content_parts.append(f"DESCRIPTION: {meta_desc.get('content')}")
        
        # Extract all headings with hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        if headings:
            content_parts.append("\n=== HEADINGS ===")
            for h in headings:
                text = h.get_text(strip=True)
                if text:
                    content_parts.append(f"{h.name.upper()}: {text}")
        
        # Extract main content
        content_parts.append("\n=== MAIN CONTENT ===")
        
        # Get paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs[:30]:
            text = p.get_text(strip=True)
            if len(text) > 20:
                content_parts.append(text)
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists[:10]:
            items = lst.find_all('li')
            for item in items[:15]:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    content_parts.append(f"• {text}")
        
        # Extract tables
        tables = soup.find_all('table')
        if tables:
            content_parts.append("\n=== TABLES ===")
            for table in tables[:3]:
                rows = table.find_all('tr')
                for row in rows[:10]:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' | '.join([cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)])
                    if row_text:
                        content_parts.append(row_text)
        
        full_content = '\n'.join(content_parts)
        return full_content[:8000]
    
    def scrape_page(self, url):
        """Scrape a single page with comprehensive extraction"""
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove unwanted tags
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
                tag.decompose()
            
            # Extract comprehensive content
            content = self.extract_comprehensive_content(soup)
            
            if not content or len(content) < 100:
                return None
            
            return {
                "url": url,
                "content": content,
                "title": soup.title.string if soup.title else "No title"
            }
        except Exception as e:
            print(f"[Scraper] Error scraping {url}: {e}")
            return None
    
    def scrape_website(self, base_url, progress_callback=None):
        """Scrape website with automatic URL discovery"""
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        # Try common pages
        urls = [
            base_url,
            f"{base_url}/about",
            f"{base_url}/about-us",
            f"{base_url}/services",
            f"{base_url}/products",
            f"{base_url}/contact",
            f"{base_url}/contact-us",
            f"{base_url}/pricing",
            f"{base_url}/faq"
        ]
        
        pages = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scrape_page, url): url for url in urls}
            for i, future in enumerate(as_completed(futures)):
                if progress_callback:
                    progress_callback(i+1, len(urls), futures[future])
                result = future.result()
                if result:
                    pages.append(result)
        
        # Extract contact info from all pages
        all_text = '\n'.join([p['content'] for p in pages])
        
        # Better email extraction
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)))[:5]
        
        # Better phone extraction
        phones = list(set(re.findall(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', all_text)))[:5]
        
        return pages, {"emails": emails, "phones": phones}

class SmartAI:
    """AI assistant with caching and proper error handling"""
    def __init__(self):
        self.cache = {}
    
    @st.cache_data(ttl=3600)
    def _cached_llm_call(_self, prompt_hash, prompt):
        """Cached LLM call to avoid repeated API requests"""
        try:
            resp = requests.post(
                OPENROUTER_API_BASE,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/yourusername",  # Required by OpenRouter
                    "X-Title": "AI Chatbot"  # Optional
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 80,  # Ultra-fast 2-second responses
                    "temperature": 0.5  # Lower for faster, focused answers
                },
                timeout=4  # Quick 2-second target
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 401:
                return "⚠️ API key error. Please check your OPENROUTER_API_KEY."
            elif resp.status_code == 429:
                return "⚠️ Rate limit reached. Please try again in a moment."
            return f"⚠️ API Error {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return f"⚠️ Connection error: {str(e)}"
    
    def call_llm(self, prompt):
        """Fast LLM call with caching"""
        if not OPENROUTER_API_KEY:
            return "⚠️ OpenRouter API key not set. Please add it to your .env file."
        
        # Check in-memory cache first
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Use Streamlit cache
        result = self._cached_llm_call(cache_key, prompt)
        
        if result and not result.startswith("⚠️"):
            self.cache[cache_key] = result
        
        return result

class UniversalChatbot:
    """Universal chatbot with enhanced scraping and AI"""
    def __init__(self, company_name, website_url, chatbot_id):
        self.company_name = company_name
        self.website_url = website_url
        self.chatbot_id = chatbot_id
        self.pages = []
        self.contact_info = {}
        self.ready = False
        self.ai = SmartAI()
    
    def initialize(self, progress_callback=None):
        """Initialize with automatic scraping"""
        try:
            scraper = EnhancedScraper()
            self.pages, self.contact_info = scraper.scrape_website(self.website_url, progress_callback)
            self.ready = True
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False
    
    def initialize_with_custom_urls(self, custom_urls, progress_callback=None):
        """Initialize with custom URLs"""
        try:
            scraper = EnhancedScraper()
            pages = []
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(scraper.scrape_page, url): url for url in custom_urls}
                for i, future in enumerate(as_completed(futures)):
                    if progress_callback:
                        progress_callback(i+1, len(custom_urls), futures[future])
                    result = future.result()
                    if result:
                        pages.append(result)
            
            # Extract contact info
            all_text = '\n'.join([p['content'] for p in pages])
            emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)))[:5]
            phones = list(set(re.findall(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', all_text)))[:5]
            
            self.pages = pages
            self.contact_info = {"emails": emails, "phones": phones}
            self.ready = True
            return True
        except Exception as e:
            print(f"Init error with custom URLs: {e}")
            return False
    
    def ask(self, question):
        """Answer user question with context"""
        if not self.ready:
            return "⚠️ Chatbot not ready. Please initialize first."
        
        # Quick responses (instant)
        if any(g in question.lower() for g in ['hi', 'hello', 'hey', 'greetings']):
            return f"👋 Hello! I'm the AI assistant for **{self.company_name}**. How can I help you?"
        
        if any(k in question.lower() for k in ['email', 'contact', 'phone', 'reach']):
            msg = f"📞 **Contact {self.company_name}**\n\n"
            if self.contact_info.get('emails'):
                msg += "📧 " + ", ".join(self.contact_info['emails']) + "\n"
            if self.contact_info.get('phones'):
                msg += "📱 " + ", ".join(self.contact_info['phones']) + "\n"
            msg += f"🌐 {self.website_url}"
            return msg
        
        # Ultra-optimized context for 2-second responses
        context = self.pages[0]['content'][:600] if self.pages else "No content"  # Single page, 600 chars max
        
        prompt = f"""You have info from {self.company_name} website:

{context}

Answer this briefly and accurately: {question}

Answer (1 sentence):
"""
        
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
    if not email or not email.strip():
        return False
    return '@' in email and '.' in email.split('@')[-1]

def validate_phone(phone):
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
    st.caption("Paste any URL and get accurate answers! Automatic lead capture after 3 questions.")
    
    if not OPENROUTER_API_KEY:
        st.error("⚠️ OPENROUTER_API_KEY not set!")
        st.info("Add this to your .env file: OPENROUTER_API_KEY=your_key_here")
        st.info("Get your free API key from: https://openrouter.ai/keys")
        return
    
    st.sidebar.title("🏢 Management")
    
    with st.sidebar.expander("➕ New Chatbot", expanded=True):
        name = st.text_input("Company Name", placeholder="e.g., TechCorp")
        url = st.text_input("Website URL", placeholder="e.g., https://example.com")
        
        # Custom URL option
        use_custom_urls = st.checkbox("🎯 Specify custom pages to scrape", value=False)
        
        custom_urls_list = []
        if use_custom_urls:
            st.caption("Enter specific URLs to scrape (one per line):")
            custom_urls_text = st.text_area(
                "Custom URLs",
                placeholder="https://example.com/about\nhttps://example.com/pricing\nhttps://example.com/faq",
                height=100,
                label_visibility="collapsed"
            )
            if custom_urls_text:
                custom_urls_list = [u.strip() for u in custom_urls_text.split('\n') if u.strip()]
        
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
                init_success = False
                
                if use_custom_urls and custom_urls_list:
                    init_success = bot.initialize_with_custom_urls(custom_urls_list, cb)
                else:
                    init_success = bot.initialize(cb)
                
                if init_success:
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
                else:
                    st.error("❌ Failed to initialize chatbot. Check the URLs.")
    
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
                    
                    if lead['timeend']:
                        duration = lead['timeend'] - lead['timestart']
                        st.write(f"**Duration:** {duration}")
                    
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
            st.caption("Any format accepted")
            phone = st.text_input("Your Phone", key="phone_input", 
                                placeholder="e.g., +1234567890")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Submit", type="primary", key="submit_phone"):
                    phone_value = phone.strip() if phone else "Not provided"
                    st.session_state.lead_data['phone'] = phone_value
                    
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
                        st.error("Database save failed.")
            
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
                        st.error("Database save failed.")
    
    # Chat Input
    if question := st.chat_input("Ask anything...", 
                                  disabled=bool(st.session_state.lead_capture_mode and not st.session_state.lead_captured)):
        if st.session_state.lead_capture_mode and not st.session_state.lead_captured:
            st.warning("⚠️ Please complete the form above")
        else:
            st.session_state.chat_history.append({"role": "user", "content": question})
            
            with st.spinner("💭"):
                answer = bot.ask(question)
            
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.session_state.question_count += 1
            
            if st.session_state.question_count >= 3 and not st.session_state.lead_captured and not st.session_state.lead_capture_mode:
                st.session_state.lead_capture_mode = 'ask_name'
            
            st.rerun()

if __name__ == "__main__":
    main()
