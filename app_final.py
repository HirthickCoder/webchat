import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import os
import hashlib
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Page configuration
st.set_page_config(
    page_title="AI Chatbot Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API key from secrets or environment
def get_secret(key, default=""):
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)

OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "google/gemma-2-9b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

# Professional CSS styling
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Stat cards */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s;
        margin: 1rem 0;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Chat messages */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        max-height: 500px;
        overflow-y: auto;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0;
        margin-left: auto;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease;
    }
    
    .bot-message {
        background: #f3f4f6;
        color: #1f2937;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 0;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        animation: slideInLeft 0.3s ease;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Chatbot cards */
    .chatbot-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e5e7eb;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .chatbot-card:hover {
        border-color: #667eea;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
        transform: translateY(-3px);
    }
    
    /* Lead cards */
    .lead-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #10b981;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .lead-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .badge-info {
        background: #dbeafe;
        color: #1e40af;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
        transition: all 0.3s;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Helper Classes
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
    
    def scrape_website(self, base_url):
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        urls = [base_url, f"{base_url}/about", f"{base_url}/services"]
        pages = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
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
            return "⚠️ Please configure OPENROUTER_API_KEY in Streamlit secrets."
        
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
                pass
            
            self.current_model_index = (self.current_model_index + 1) % len(MODELS)
        
        return "I'm having trouble connecting to the AI service. Please try again."

# Initialize session state
def init_session():
    defaults = {
        'chatbots': {},
        'current_view': 'dashboard',
        'selected_chatbot': None,
        'chat_history': [],
        'question_count': 0,
        'lead_captured': False,
        'session_id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16],
        'conversation_start': None,
        'leads': [],
        'ai_engine': SmartAI()
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Dashboard View
def show_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Chatbot Platform</h1>
        <p>Intelligent conversational AI with advanced lead capture</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Leads</div>
            <div class="stat-number">{len(st.session_state.leads)}</div>
            <div style="color: #10b981;">↑ Active</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_questions = sum(lead.get('questions', 0) for lead in st.session_state.leads)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Questions Asked</div>
            <div class="stat-number">{total_questions}</div>
            <div style="color: #667eea;">Total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_q = total_questions / len(st.session_state.leads) if st.session_state.leads else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Avg. Questions</div>
            <div class="stat-number">{avg_q:.1f}</div>
            <div style="color: #10b981;">Per Lead</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Bots</div>
            <div class="stat-number">{len(st.session_state.chatbots)}</div>
            <div style="color: #f59e0b;">Online</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Recent Leads")
        if st.session_state.leads:
            for lead in st.session_state.leads[-5:][::-1]:
                st.markdown(f"""
                <div class="lead-card">
                    <h4 style="margin: 0;">👤 {lead.get('name', 'Anonymous')}</h4>
                    <p style="margin: 0.5rem 0; color: #6b7280;">📧 {lead.get('email', 'N/A')}</p>
                    <p style="margin: 0.5rem 0; color: #6b7280;">🏢 {lead.get('company', 'N/A')}</p>
                    <span class="badge badge-success">{lead.get('questions', 0)} Questions</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("💡 No leads yet. Create a chatbot and start chatting!")
    
    with col2:
        st.subheader("🤖 Active Chatbots")
        if st.session_state.chatbots:
            for key, bot in st.session_state.chatbots.items():
                st.markdown(f"""
                <div class="chatbot-card">
                    <h4 style="margin: 0;">💬 {bot['name']}</h4>
                    <p style="margin: 0.5rem 0; font-size: 0.85rem; color: #6b7280;">🌐 {bot['url'][:30]}...</p>
                    <span class="badge badge-success">Active</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Create your first chatbot to get started!")

# Chatbot Management
def show_chatbot_management():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Chatbot Management</h1>
        <p>Create and manage your AI chatbots</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Create New Chatbot")
        
        with st.form("create_chatbot"):
            company_name = st.text_input("🏢 Company Name", placeholder="e.g., TechCorp Solutions")
            website_url = st.text_input("🌐 Website URL", placeholder="https://example.com")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("✨ Create Chatbot", use_container_width=True)
            with col_b:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit and company_name and website_url:
                with st.spinner("🔄 Creating chatbot..."):
                    progress = st.progress(0)
                    status = st.empty()
                    
                    status.text("📡 Connecting to website...")
                    progress.progress(25)
                    time.sleep(0.5)
                    
                    status.text("🔍 Scraping content...")
                    progress.progress(50)
                    
                    try:
                        scraper = EnhancedScraper()
                        pages, contact_info = scraper.scrape_website(website_url)
                        
                        if pages:
                            chatbot_id = hashlib.md5(f"{company_name}{time.time()}".encode()).hexdigest()[:12]
                            slug = re.sub(r'[^a-z0-9]+', '-', company_name.lower())
                            
                            st.session_state.chatbots[slug] = {
                                'id': chatbot_id,
                                'name': company_name,
                                'url': website_url,
                                'pages': pages,
                                'contact_info': contact_info,
                                'created': datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            
                            progress.progress(100)
                            status.text("✅ Chatbot created successfully!")
                            st.success(f"✅ Chatbot '{company_name}' created successfully!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Failed to scrape website. Please check the URL.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("📊 Quick Stats")
        st.metric("Total Chatbots", len(st.session_state.chatbots))
        st.metric("Active", len(st.session_state.chatbots))
    
    st.markdown("---")
    
    # List chatbots
    if st.session_state.chatbots:
        st.subheader("📋 Your Chatbots")
        for key, bot in st.session_state.chatbots.items():
            with st.expander(f"💬 {bot['name']} - {bot['id']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**🌐 Website:** {bot['url']}")
                    st.write(f"**📅 Created:** {bot['created']}")
                
                with col2:
                    st.write(f"**🆔 ID:** {bot['id']}")
                    st.write(f"**📊 Status:** Active")
                
                with col3:
                    if st.button(f"💬 Test Chat", key=f"test_{key}"):
                        st.session_state.selected_chatbot = key
                        st.session_state.current_view = 'chat'
                        st.session_state.chat_history = []
                        st.session_state.question_count = 0
                        st.session_state.lead_captured = False
                        st.rerun()
                    
                    if st.button(f"🗑️ Delete", key=f"del_{key}"):
                        del st.session_state.chatbots[key]
                        st.rerun()

# Chat Interface
def show_chat_interface():
    if not st.session_state.selected_chatbot or st.session_state.selected_chatbot not in st.session_state.chatbots:
        st.warning("⚠️ Please select a chatbot first")
        if st.button("← Back to Dashboard"):
            st.session_state.current_view = 'dashboard'
            st.rerun()
        return
    
    bot = st.session_state.chatbots[st.session_state.selected_chatbot]
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="main-header">
            <h1>💬 {bot['name']}</h1>
            <p>AI-Powered Customer Support</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Questions", st.session_state.question_count)
    
    with col3:
        if st.session_state.lead_captured:
            st.success("✅ Lead")
        else:
            st.info("🎯 Active")
    
    # Chat messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lead capture form
    if st.session_state.question_count >= 3 and not st.session_state.lead_captured:
        st.markdown("---")
        st.subheader("🎯 Quick Contact Information")
        
        with st.form("lead_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("👤 Name", placeholder="John Doe")
                email = st.text_input("📧 Email", placeholder="john@example.com")
            
            with col2:
                phone = st.text_input("📱 Phone", placeholder="+1234567890")
                company = st.text_input("🏢 Company", placeholder="Your Company")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("✅ Submit", use_container_width=True)
            with col_b:
                skipped = st.form_submit_button("⏭️ Skip", use_container_width=True)
            
            if submitted or skipped:
                lead = {
                    'name': name or 'Anonymous',
                    'email': email or 'not_provided@example.com',
                    'phone': phone or 'Not provided',
                    'company': company or bot['name'],
                    'questions': st.session_state.question_count,
                    'conversation': st.session_state.chat_history,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.leads.append(lead)
                st.session_state.lead_captured = True
                st.success("✅ Thank you! We'll get back to you soon.")
                st.balloons()
                time.sleep(2)
                st.rerun()
    
    # Chat input
    st.markdown("---")
    user_input = st.text_input("💬 Type your message...", key="chat_input", placeholder="Ask me anything...")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)
    
    if (send_button or user_input) and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Generate response
        with st.spinner("🤖 Thinking..."):
            # Handle greetings
            if any(g in user_input.lower() for g in ['hi', 'hello', 'hey']):
                response = f"👋 Hello! I'm the AI assistant for **{bot['name']}**. How can I help you today?"
            # Handle contact requests
            elif any(k in user_input.lower() for k in ['email', 'contact', 'phone']):
                contact_info = bot.get('contact_info', {})
                response = f"📞 **Contact {bot['name']}**\n\n"
                if contact_info.get('emails'):
                    response += "📧 " + ", ".join(contact_info['emails']) + "\n"
                if contact_info.get('phones'):
                    response += "📱 " + ", ".join(contact_info['phones']) + "\n"
                response += f"🌐 {bot['url']}"
            else:
                # Use AI
                context = bot['pages'][0]['content'][:800] if bot['pages'] else "No content"
                prompt = f"""You are a helpful AI assistant for {bot['name']}.

Company Information:
{context}

User Question: {user_input}

Provide a helpful, concise answer (2-3 sentences):"""
                
                response = st.session_state.ai_engine.call_llm(prompt)
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        st.session_state.question_count += 1
        st.rerun()
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()

# Leads View
def show_leads():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Lead Management</h1>
        <p>View and manage captured leads</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.leads:
        for lead in st.session_state.leads[::-1]:
            with st.expander(f"🎯 {lead['name']} - {lead['company']} ({lead['timestamp']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**👤 Name:** {lead['name']}")
                    st.write(f"**📧 Email:** {lead['email']}")
                    st.write(f"**📱 Phone:** {lead['phone']}")
                
                with col2:
                    st.write(f"**🏢 Company:** {lead['company']}")
                    st.write(f"**💬 Questions:** {lead['questions']}")
                    st.write(f"**📅 Time:** {lead['timestamp']}")
                
                if lead.get('conversation'):
                    st.subheader("💬 Conversation")
                    for msg in lead['conversation']:
                        if msg['role'] == 'user':
                            st.markdown(f"**👤 User:** {msg['content']}")
                        else:
                            st.markdown(f"**🤖 Bot:** {msg['content']}")
    else:
        st.info("📭 No leads captured yet. Start chatting to generate leads!")

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🎯 Navigation")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    if st.button("🤖 Chatbots", use_container_width=True):
        st.session_state.current_view = 'chatbots'
        st.rerun()
    
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.current_view = 'chat'
        st.rerun()
    
    if st.button("📊 Leads", use_container_width=True):
        st.session_state.current_view = 'leads'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ Info")
    st.info(f"**Active Bots:** {len(st.session_state.chatbots)}")
    st.info(f"**Total Leads:** {len(st.session_state.leads)}")
    
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    if OPENROUTER_API_KEY:
        st.success("✅ Connected")
    else:
        st.error("❌ Not configured")

# Main routing
if st.session_state.current_view == 'dashboard':
    show_dashboard()
elif st.session_state.current_view == 'chatbots':
    show_chatbot_management()
elif st.session_state.current_view == 'chat':
    show_chat_interface()
elif st.session_state.current_view == 'leads':
    show_leads()
else:
    show_dashboard() 
