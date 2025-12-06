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

# Dark theme configuration
st.set_page_config(
    page_title="AI Chat Helper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API key
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

# Modern dark theme CSS
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Sidebar dark theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 100%);
        border-right: 1px solid #2d2d44;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(to right, #fff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(30, 30, 46, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* User message */
    .user-msg {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px 16px 4px 16px;
        margin: 1rem 0;
        margin-left: auto;
        max-width: 70%;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        animation: slideInRight 0.3s ease;
    }
    
    /* Bot message */
    .bot-msg {
        background: rgba(45, 45, 68, 0.8);
        color: #e0e7ff;
        padding: 1rem 1.5rem;
        border-radius: 16px 16px 16px 4px;
        margin: 1rem 0;
        max-width: 70%;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
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
    
    /* Code blocks */
    .code-block {
        background: #1e1e2e;
        border: 1px solid #6366f1;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        color: #a5b4fc;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        background: rgba(30, 30, 46, 0.8);
        border: 2px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        color: white;
        padding: 0.75rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    
    /* Cards */
    .stat-card {
        background: rgba(30, 30, 46, 0.6);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: #6366f1;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(to right, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Sidebar items */
    .sidebar-item {
        background: rgba(99, 102, 241, 0.1);
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #6366f1;
        color: #e0e7ff;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 30, 46, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #6366f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

# Helper Classes
class EnhancedScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
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
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
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
            return "⚠️ Please configure API key in secrets"
        
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
            except:
                pass
            
            self.current_model_index = (self.current_model_index + 1) % len(MODELS)
        
        return "I'm having trouble connecting. Please try again."

# Initialize session
def init_session():
    defaults = {
        'chatbots': {},
        'current_view': 'chat',
        'selected_chatbot': None,
        'chat_history': [],
        'question_count': 0,
        'lead_captured': False,
        'leads': [],
        'ai_engine': SmartAI()
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-item"><h2 style="margin:0;">🤖 AI Chat Helper</h2></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("💬 New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.question_count = 0
        st.session_state.lead_captured = False
        st.rerun()
    
    if st.button("🤖 Create Chatbot", use_container_width=True):
        st.session_state.current_view = 'create'
        st.rerun()
    
    if st.button("📊 View Leads", use_container_width=True):
        st.session_state.current_view = 'leads'
        st.rerun()
    
    st.markdown("---")
    st.markdown('<div class="sidebar-item">', unsafe_allow_html=True)
    st.markdown(f"**Active Bots:** {len(st.session_state.chatbots)}")
    st.markdown(f"**Total Leads:** {len(st.session_state.leads)}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    if OPENROUTER_API_KEY:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Not Set")

# Main content
if st.session_state.current_view == 'create':
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Create AI Chatbot</h1>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">Build intelligent chatbot for your website</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        company_name = st.text_input("🏢 Company Name", placeholder="e.g., TechCorp")
        website_url = st.text_input("🌐 Website URL", placeholder="https://example.com")
        
        if st.button("✨ Create Chatbot", use_container_width=True):
            if company_name and website_url:
                with st.spinner("🔄 Creating chatbot..."):
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
                                'contact_info': contact_info
                            }
                            
                            st.session_state.selected_chatbot = slug
                            st.session_state.current_view = 'chat'
                            st.success("✅ Chatbot created!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to scrape website")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div style="color:#a5b4fc; margin-bottom:0.5rem;">Quick Stats</div>
            <div class="stat-number">{}</div>
            <div style="color:#6b7280;">Total Chatbots</div>
        </div>
        """.format(len(st.session_state.chatbots)), unsafe_allow_html=True)

elif st.session_state.current_view == 'leads':
    st.markdown("""
    <div class="main-header">
        <h1>📊 Lead Management</h1>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">View captured leads</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.leads:
        for lead in st.session_state.leads[::-1]:
            with st.expander(f"🎯 {lead['name']} - {lead.get('company', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**📧 Email:** {lead['email']}")
                    st.write(f"**📱 Phone:** {lead.get('phone', 'N/A')}")
                with col2:
                    st.write(f"**💬 Questions:** {lead.get('questions', 0)}")
                    st.write(f"**📅 Time:** {lead.get('timestamp', 'N/A')}")
    else:
        st.info("📭 No leads yet")

else:  # Chat view
    if st.session_state.selected_chatbot and st.session_state.selected_chatbot in st.session_state.chatbots:
        bot = st.session_state.chatbots[st.session_state.selected_chatbot]
        
        st.markdown(f"""
        <div class="main-header">
            <h1>💬 {bot['name']}</h1>
            <p style="margin:0.5rem 0 0 0; opacity:0.9;">AI-Powered Assistant</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <h1>💬 AI Chat Helper</h1>
            <p style="margin:0.5rem 0 0 0; opacity:0.9;">Create a chatbot to start</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center; padding:3rem; color:#6b7280;">Start a conversation...</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lead capture
    if st.session_state.question_count >= 3 and not st.session_state.lead_captured:
        st.markdown("---")
        st.subheader("🎯 Quick Contact")
        
        with st.form("lead_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="john@example.com")
            with col2:
                phone = st.text_input("Phone", placeholder="+1234567890")
                company = st.text_input("Company", placeholder="Your Company")
            
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
                    'company': company or 'N/A',
                    'questions': st.session_state.question_count,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.leads.append(lead)
                st.session_state.lead_captured = True
                st.success("✅ Thank you!")
                st.balloons()
                time.sleep(1)
                st.rerun()
    
    # Chat input
    st.markdown("---")
    user_input = st.text_input("💬 Type your message...", key="chat_input", placeholder="Ask me anything...")
    
    if st.button("📤 Send", use_container_width=True) and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        with st.spinner("🤖 Thinking..."):
            if any(g in user_input.lower() for g in ['hi', 'hello', 'hey']):
                response = "👋 Hello! How can I help you today?"
            elif st.session_state.selected_chatbot and st.session_state.selected_chatbot in st.session_state.chatbots:
                bot = st.session_state.chatbots[st.session_state.selected_chatbot]
                context = bot['pages'][0]['content'][:800] if bot['pages'] else "No content"
                prompt = f"""You are a helpful AI assistant.

Context: {context}

Question: {user_input}

Answer (2-3 sentences):"""
                response = st.session_state.ai_engine.call_llm(prompt)
            else:
                response = "Please create a chatbot first to get started!"
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        st.session_state.question_count += 1
        st.rerun()
