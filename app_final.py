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

# Mobile-style app configuration
st.set_page_config(
    page_title="AI Chat Pro",
    page_icon="🤖",
    layout="centered",
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

# Mobile-style CSS with robot character
st.markdown("""
<style>
    /* Mobile app theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        max-width: 450px;
        margin: 0 auto;
    }
    
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Robot character container */
    .robot-container {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #1a3a52 0%, #2d5f7a 100%);
        border-radius: 24px;
        margin: 1rem 0;
        border: 2px solid rgba(52, 211, 153, 0.3);
        box-shadow: 0 8px 32px rgba(52, 211, 153, 0.2);
    }
    
    .robot-emoji {
        font-size: 8rem;
        margin: 1rem 0;
        filter: drop-shadow(0 0 20px rgba(52, 211, 153, 0.5));
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    /* Title styling */
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        text-align: center;
        margin: 1rem 0;
        background: linear-gradient(to right, #34d399, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .app-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(52, 211, 153, 0.2);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s;
    }
    
    .feature-card:hover {
        border-color: #34d399;
        transform: translateX(5px);
        box-shadow: 0 4px 20px rgba(52, 211, 153, 0.3);
    }
    
    .feature-icon {
        font-size: 2rem;
        min-width: 50px;
    }
    
    .feature-text {
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    /* Pricing card */
    .pricing-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 2px solid #34d399;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 8px 32px rgba(52, 211, 153, 0.3);
    }
    
    .price {
        font-size: 2.5rem;
        font-weight: 700;
        color: #34d399;
        margin: 1rem 0;
    }
    
    .price-subtitle {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Chat bubble */
    .chat-bubble {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(52, 211, 153, 0.3);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #e2e8f0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
        color: white;
        border: none;
        margin-left: 2rem;
    }
    
    .bot-bubble {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(52, 211, 153, 0.3);
        margin-right: 2rem;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 20px rgba(52, 211, 153, 0.4);
        text-transform: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 28px rgba(52, 211, 153, 0.6);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        background: rgba(30, 41, 59, 0.8);
        border: 2px solid rgba(52, 211, 153, 0.3);
        border-radius: 16px;
        color: white;
        padding: 1rem;
        font-size: 1rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #34d399;
        box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.2);
    }
    
    /* Character selector */
    .character-card {
        background: rgba(30, 41, 59, 0.6);
        border: 2px solid rgba(52, 211, 153, 0.2);
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .character-card:hover {
        border-color: #34d399;
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(52, 211, 153, 0.4);
    }
    
    .character-emoji {
        font-size: 3rem;
        margin: 0.5rem 0;
    }
    
    .character-name {
        color: #e2e8f0;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .character-role {
        color: #94a3b8;
        font-size: 0.85rem;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #34d399;
        border-radius: 3px;
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
        
        urls = [base_url]
        pages = []
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(self.scrape_page, base_url).result()
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
        'view': 'welcome',
        'selected_character': None,
        'chatbot': None,
        'chat_history': [],
        'ai_engine': SmartAI()
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Welcome screen
if st.session_state.view == 'welcome':
    st.markdown("""
    <div class="robot-container">
        <div class="robot-emoji">🤖</div>
        <h2 style="color: white; margin: 0;">AI Chat Pro</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="app-subtitle">Your AI assistant that can quickly respond to any of your questions. Whether you need help with homework, a coding doubt, virtual doctor, or anyone else you may think of, Chat with us!</div>', unsafe_allow_html=True)
    
    # Features
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🚫</div>
        <div class="feature-text"><strong>No limitation</strong></div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">🚫</div>
        <div class="feature-text"><strong>No Ads</strong></div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-text"><strong>All Functions</strong></div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">❌</div>
        <div class="feature-text"><strong>Cancel Anytime</strong></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pricing
    st.markdown("""
    <div class="pricing-card">
        <div class="price-subtitle">Free Forever</div>
        <div class="price">$0</div>
        <div class="price-subtitle">No credit card required</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Continue >>>"):
        st.session_state.view = 'characters'
        st.rerun()

# Character selection
elif st.session_state.view == 'characters':
    st.markdown('<div class="app-title">Choose Your AI Assistant</div>', unsafe_allow_html=True)
    
    characters = [
        {"emoji": "👨‍💼", "name": "Name Generator", "role": "Translator"},
        {"emoji": "👨‍💻", "name": "Prompt Engineer", "role": "Writer"},
        {"emoji": "🤖", "name": "AI Chat Pro", "role": "Interviewer"},
        {"emoji": "⚕️", "name": "Virtual Doctor", "role": "Mental Health Advisor"},
        {"emoji": "🔮", "name": "Astrologer", "role": "Any Character"}
    ]
    
    cols = st.columns(2)
    for idx, char in enumerate(characters):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="character-card">
                <div class="character-emoji">{char['emoji']}</div>
                <div class="character-name">{char['name']}</div>
                <div class="character-role">{char['role']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select {char['name']}", key=f"char_{idx}", use_container_width=True):
                st.session_state.selected_character = char
                st.session_state.view = 'setup'
                st.rerun()

# Setup chatbot
elif st.session_state.view == 'setup':
    char = st.session_state.selected_character
    
    st.markdown(f"""
    <div class="robot-container">
        <div class="robot-emoji">{char['emoji']}</div>
        <h2 style="color: white; margin: 0.5rem 0;">{char['name']}</h2>
        <p style="color: #94a3b8; margin: 0;">{char['role']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="app-subtitle">Enter a website URL to train your AI assistant</div>', unsafe_allow_html=True)
    
    website_url = st.text_input("🌐 Website URL", placeholder="https://example.com", label_visibility="collapsed")
    
    if st.button("Start Chatting"):
        if website_url:
            with st.spinner("🔄 Training AI..."):
                try:
                    scraper = EnhancedScraper()
                    pages, _ = scraper.scrape_website(website_url)
                    
                    if pages:
                        st.session_state.chatbot = {
                            'character': char,
                            'url': website_url,
                            'pages': pages
                        }
                        st.session_state.view = 'chat'
                        st.success("✅ Ready!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Couldn't access website")
                except:
                    st.error("❌ Error occurred")
        else:
            st.warning("⚠️ Please enter a URL")

# Chat interface
elif st.session_state.view == 'chat':
    bot = st.session_state.chatbot
    char = bot['character']
    
    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("←"):
            st.session_state.view = 'characters'
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        st.markdown(f'<div style="text-align:center; color:white; font-weight:600;">{char["name"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat messages
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-bubble user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble bot-bubble">{char["emoji"]} {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="robot-container">
            <div class="robot-emoji">{char['emoji']}</div>
            <div style="color: #94a3b8;">How can I assist you?</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Input
    st.markdown("---")
    user_input = st.text_input("💬 Type your message...", placeholder="Ask me anything...", label_visibility="collapsed")
    
    if st.button("Send 📤") and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        with st.spinner("🤖 Thinking..."):
            if any(g in user_input.lower() for g in ['hi', 'hello', 'hey']):
                response = f"👋 Hello! I'm {char['name']}, your {char['role']}. How can I help you?"
            else:
                context = bot['pages'][0]['content'][:800] if bot['pages'] else "No content"
                prompt = f"""You are {char['name']}, a helpful {char['role']}.

Context: {context}

Question: {user_input}

Answer (2-3 sentences):"""
                response = st.session_state.ai_engine.call_llm(prompt)
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        st.rerun()
