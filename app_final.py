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

# Professional landing page configuration
st.set_page_config(
    page_title="Botify Cloud - AI Chatbot Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# Professional landing page CSS
st.markdown("""
<style>
    /* Dark professional theme */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2f3a 100%);
    }
    
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Hero section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-radius: 24px;
        margin: 2rem 0;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin: 1rem 0;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #94a3b8;
        margin: 1rem 0 2rem 0;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .gradient-text {
        background: linear-gradient(to right, #10b981, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Robot image container */
    .robot-showcase {
        text-align: center;
        padding: 3rem 0;
        position: relative;
    }
    
    .robot-image {
        max-width: 500px;
        width: 100%;
        filter: drop-shadow(0 0 40px rgba(16, 185, 129, 0.5));
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(2deg); }
    }
    
    /* Feature cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 2rem;
        margin: 3rem 0;
    }
    
    .feature-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 20px;
        padding: 2rem;
        transition: all 0.3s;
        text-align: center;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        border-color: #10b981;
        box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: white;
        margin: 1rem 0;
    }
    
    .feature-desc {
        color: #94a3b8;
        line-height: 1.6;
    }
    
    /* Stats section */
    .stats-container {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        padding: 3rem;
        margin: 3rem 0;
        text-align: center;
    }
    
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }
    
    .stat-item {
        padding: 1.5rem;
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(to right, #10b981, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* CTA buttons */
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1rem 3rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 32px rgba(16, 185, 129, 0.6);
    }
    
    /* Dashboard preview */
    .dashboard-preview {
        background: rgba(30, 41, 59, 0.8);
        border: 2px solid rgba(16, 185, 129, 0.3);
        border-radius: 24px;
        padding: 2rem;
        margin: 3rem 0;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }
    
    .dashboard-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(16, 185, 129, 0.1);
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #10b981;
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Trusted by section */
    .trusted-section {
        text-align: center;
        padding: 3rem 0;
        margin: 3rem 0;
    }
    
    .company-logos {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        flex-wrap: wrap;
        margin-top: 2rem;
        opacity: 0.6;
    }
    
    .company-logo {
        font-size: 1.5rem;
        color: #94a3b8;
        font-weight: 600;
    }
    
    /* Chat bubbles */
    .chat-bubble {
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        max-width: 70%;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        color: white;
        margin-left: auto;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }
    
    .bot-bubble {
        background: rgba(30, 41, 59, 0.8);
        color: #e2e8f0;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# Helper Classes (same as before)
class EnhancedScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.timeout = 8
    
    def extract_content(self, soup):
        content_parts = []
        if soup.title:
            content_parts.append(f"TITLE: {soup.title.string}")
        
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for h in headings[:10]:
            text = h.get_text(strip=True)
            if text:
                content_parts.append(f"{h.name.upper()}: {text}")
        
        paragraphs = soup.find_all('p')
        for p in paragraphs[:15]:
            text = p.get_text(strip=True)
            if len(text) > 20:
                content_parts.append(text)
        
        return '\n'.join(content_parts)[:3000]
    
    def scrape_page(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            content = self.extract_content(soup)
            return {"url": url, "content": content} if content and len(content) > 100 else None
        except:
            return None
    
    def scrape_website(self, base_url):
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        pages = []
        result = self.scrape_page(base_url)
        if result:
            pages.append(result)
        
        return pages, {}

class SmartAI:
    def __init__(self):
        self.cache = {}
        self.current_model_index = 0
    
    def call_llm(self, prompt):
        if not OPENROUTER_API_KEY:
            return "⚠️ Please configure API key"
        
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
                        "Content-Type": "application/json"
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
                    if "choices" in data:
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
        'view': 'landing',
        'chatbot': None,
        'chat_history': [],
        'ai_engine': SmartAI(),
        'leads': []
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Landing page
if st.session_state.view == 'landing':
    # Hero section
    st.markdown("""
    <div class="hero-section">
        <div style="display: inline-block; background: rgba(16, 185, 129, 0.2); padding: 0.5rem 1.5rem; border-radius: 50px; margin-bottom: 1rem;">
            <span style="color: #10b981; font-weight: 600;">✨ Create Automated Chatbots</span>
        </div>
        <h1 class="hero-title">
            Botify Cloud Is The Ultimate<br/>
            <span class="gradient-text">Shopify For Crypto World</span>
        </h1>
        <p class="hero-subtitle">
            Botify cloud is an innovative platform designed to streamline and simplify cryptocurrency automation through seamless, all-in-one AI Agents.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.view = 'create'
            st.rerun()
    
    # Robot showcase with generated image
    st.markdown('<div class="robot-showcase">', unsafe_allow_html=True)
    
    # Display generated robot image
    try:
        st.image("C:/Users/Hirthick/.gemini/antigravity/brain/9eea7aa3-9ff6-4103-8f77-0240671bd9cb/robot_assistant_3d.png", 
                 use_container_width=False, width=500)
    except:
        st.markdown('<div class="robot-image" style="font-size: 15rem; text-align: center;">🤖</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats section
    st.markdown("""
    <div class="stats-container">
        <h2 style="color: white; font-size: 2rem; margin-bottom: 1rem;">Hold $Botify and earn lifetime rewards!</h2>
        <div class="stat-grid">
            <div class="stat-item">
                <div class="stat-number">$9,961.28</div>
                <div class="stat-label">Amount Earned</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">12</div>
                <div class="stat-label">Pending Payouts</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">73</div>
                <div class="stat-label">Completed Payouts</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features section
    st.markdown('<h2 style="text-align: center; color: white; font-size: 2.5rem; margin: 4rem 0 2rem 0;">Key Botify.Cloud Features</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">Agent Creation</div>
            <div class="feature-desc">Effortlessly create custom agents to generate leads through intelligent web scraping</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">AI Chat Assistant</div>
            <div class="feature-desc">Intelligent AI-powered conversations with context awareness and natural language</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Lead Management</div>
            <div class="feature-desc">Capture and manage leads automatically after meaningful conversations</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Lightning Fast</div>
            <div class="feature-desc">2-3 second response times with multi-model AI fallback system</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <div class="feature-title">Web Scraping</div>
            <div class="feature-desc">Automatically extract content from websites to train your chatbot</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">Secure & Private</div>
            <div class="feature-desc">Your data is encrypted and secure with enterprise-grade protection</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Trusted by section
    st.markdown("""
    <div class="trusted-section">
        <h3 style="color: #94a3b8; font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;">Trusted By Leading Companies</h3>
        <div class="company-logos">
            <div class="company-logo">Shopify</div>
            <div class="company-logo">Instagram</div>
            <div class="company-logo">HubSpot</div>
            <div class="company-logo">Amazon</div>
            <div class="company-logo">Coinbase</div>
            <div class="company-logo">Dribbble</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Create chatbot view
elif st.session_state.view == 'create':
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Create Your <span class="gradient-text">AI Agent</span></h1>
        <p class="hero-subtitle">Build an intelligent chatbot in seconds</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        company_name = st.text_input("🏢 Company Name", placeholder="e.g., TechCorp")
        website_url = st.text_input("🌐 Website URL", placeholder="https://example.com")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✨ Create Agent", use_container_width=True):
                if company_name and website_url:
                    with st.spinner("🔄 Creating agent..."):
                        try:
                            scraper = EnhancedScraper()
                            pages, _ = scraper.scrape_website(website_url)
                            
                            if pages and len(pages) > 0:
                                st.session_state.chatbot = {
                                    'name': company_name,
                                    'url': website_url,
                                    'pages': pages
                                }
                                st.session_state.view = 'chat'
                                st.success("✅ Agent created!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ Couldn't scrape {website_url}. Please check the URL and try again.")
                        except requests.exceptions.Timeout:
                            st.error("❌ Website took too long to respond. Try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to website. Check your internet connection.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)[:100]}")
                else:
                    st.warning("⚠️ Please enter both company name and website URL")
        
        with col_b:
            if st.button("← Back", use_container_width=True):
                st.session_state.view = 'landing'
                st.rerun()

# Chat view
elif st.session_state.view == 'chat':
    # Check if chatbot exists
    if not st.session_state.chatbot:
        st.error("❌ No chatbot found. Please create one first.")
        if st.button("← Back to Create"):
            st.session_state.view = 'create'
            st.rerun()
        st.stop()
    
    bot = st.session_state.chatbot
    
    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Back"):
            st.session_state.view = 'landing'
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        st.markdown(f'<h2 style="text-align:center; color:white;">{bot["name"]} AI Assistant</h2>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat messages
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-bubble user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble bot-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#94a3b8;">
            <div style="font-size:5rem; margin-bottom:1rem;">🤖</div>
            <div>How can I assist you today?</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Input
    st.markdown("---")
    user_input = st.text_input("💬 Type your message...", placeholder="Ask me anything...", label_visibility="collapsed")
    
    if st.button("Send 📤") and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        with st.spinner("🤖 Thinking..."):
            if any(g in user_input.lower() for g in ['hi', 'hello', 'hey']):
                response = f"👋 Hello! I'm the AI assistant for {bot['name']}. How can I help you?"
            else:
                context = bot['pages'][0]['content'][:800] if bot.get('pages') and len(bot['pages']) > 0 else "No content available"
                prompt = f"""You are a helpful AI assistant for {bot['name']}.

Context: {context}

Question: {user_input}

Answer (2-3 sentences):"""
                response = st.session_state.ai_engine.call_llm(prompt)
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        st.rerun()

