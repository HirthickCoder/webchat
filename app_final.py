import streamlit as st
import requests
import json
from datetime import datetime
import hashlib
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="AI Chatbot Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Flask API Configuration
FLASK_API_URL = "http://localhost:5000/api"

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom containers */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #6366f1;
        transition: transform 0.2s;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .chat-container {
        background: #f8fafc;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background: white;
        color: #1f2937;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
    }
    
    .lead-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #10b981;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .lead-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    .chatbot-card {
        background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e5e7eb;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .chatbot-card:hover {
        border-color: #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
        transform: translateY(-3px);
    }
    
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .success-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .warning-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        'current_view': 'dashboard',
        'selected_chatbot': None,
        'chat_history': [],
        'session_id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16],
        'question_count': 0,
        'lead_captured': False,
        'conversation_start': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# API Helper Functions
def api_request(endpoint, method='GET', data=None):
    """Make API request to Flask backend"""
    try:
        url = f"{FLASK_API_URL}/{endpoint}"
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to Flask backend. Make sure it's running on http://localhost:5000")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Dashboard View
def show_dashboard():
    st.markdown('<div class="main-header"><h1>🤖 AI Chatbot Platform</h1><p>Intelligent conversational AI with advanced lead capture</p></div>', unsafe_allow_html=True)
    
    # Fetch stats
    stats_data = api_request('stats')
    
    if stats_data and stats_data.get('success'):
        stats = stats_data.get('stats', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #6366f1; margin: 0;">📊 Total Leads</h3>
                <h1 style="margin: 0.5rem 0;">{stats.get('total_leads', 0)}</h1>
                <p style="color: #10b981; margin: 0;">↑ Active</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #8b5cf6; margin: 0;">💬 Questions</h3>
                <h1 style="margin: 0.5rem 0;">{stats.get('total_questions', 0)}</h1>
                <p style="color: #6366f1; margin: 0;">Total Asked</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #10b981; margin: 0;">📈 Avg. Q/Lead</h3>
                <h1 style="margin: 0.5rem 0;">{stats.get('avg_questions', 0)}</h1>
                <p style="color: #10b981; margin: 0;">Per conversation</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #f59e0b; margin: 0;">⚡ Chatbots</h3>
                <h1 style="margin: 0.5rem 0;">{len(get_all_chatbots())}</h1>
                <p style="color: #10b981; margin: 0;">Active</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Recent Activity")
        leads_data = api_request('leads')
        
        if leads_data and leads_data.get('success'):
            leads = leads_data.get('leads', [])[:5]
            
            if leads:
                for lead in leads:
                    st.markdown(f"""
                    <div class="lead-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: #1f2937;">👤 {lead.get('username', 'Anonymous')}</h4>
                                <p style="margin: 0.25rem 0; color: #6b7280;">📧 {lead.get('mailid', 'N/A')}</p>
                                <p style="margin: 0.25rem 0; color: #6b7280;">🏢 {lead.get('company_name', 'N/A')}</p>
                            </div>
                            <div style="text-align: right;">
                                <span class="success-badge">{lead.get('questions_asked', 0)} Questions</span>
                                <p style="margin: 0.5rem 0; color: #9ca3af; font-size: 0.875rem;">{lead.get('timestart', 'N/A')}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No leads captured yet. Create a chatbot to get started!")
    
    with col2:
        st.subheader("🤖 Active Chatbots")
        chatbots = get_all_chatbots()
        
        if chatbots:
            for bot in chatbots:
                st.markdown(f"""
                <div class="chatbot-card">
                    <h4 style="margin: 0; color: #1f2937;">💬 {bot.get('company_name', 'Unknown')}</h4>
                    <p style="margin: 0.5rem 0; color: #6b7280; font-size: 0.875rem;">🌐 {bot.get('website_url', 'N/A')[:30]}...</p>
                    <span class="success-badge">Active</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No chatbots yet. Create one to start!")

# Chatbot Management View
def show_chatbot_management():
    st.markdown('<div class="main-header"><h1>🤖 Chatbot Management</h1><p>Create and manage your AI chatbots</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Create New Chatbot")
        
        with st.form("create_chatbot_form"):
            company_name = st.text_input("🏢 Company Name", placeholder="e.g., TechCorp Solutions")
            website_url = st.text_input("🌐 Website URL", placeholder="https://example.com")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("✨ Create Chatbot", use_container_width=True)
            with col_b:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit and company_name and website_url:
                with st.spinner("🔄 Creating chatbot and scraping website..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📡 Connecting to website...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    status_text.text("🔍 Scraping content...")
                    progress_bar.progress(50)
                    
                    result = api_request('chatbot/create', method='POST', data={
                        'company_name': company_name,
                        'website_url': website_url
                    })
                    
                    progress_bar.progress(75)
                    status_text.text("💾 Saving to database...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(100)
                    
                    if result and result.get('success'):
                        st.success(f"✅ Chatbot created successfully! ID: {result.get('chatbot_id')}")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to create chatbot. Please try again.")
    
    with col2:
        st.subheader("📊 Quick Stats")
        chatbots = get_all_chatbots()
        st.metric("Total Chatbots", len(chatbots))
        st.metric("Active Status", f"{len([b for b in chatbots if b.get('status') == 'active'])}/{len(chatbots)}")
    
    st.markdown("---")
    
    # List existing chatbots
    st.subheader("📋 Your Chatbots")
    chatbots = get_all_chatbots()
    
    if chatbots:
        for bot in chatbots:
            with st.expander(f"💬 {bot.get('company_name')} - {bot.get('chatbot_id')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**🌐 Website:** {bot.get('website_url')}")
                    st.write(f"**📅 Created:** {bot.get('created_at')}")
                
                with col2:
                    st.write(f"**🆔 ID:** {bot.get('chatbot_id')}")
                    st.write(f"**📊 Status:** {bot.get('status')}")
                
                with col3:
                    if st.button(f"💬 Test Chat", key=f"test_{bot.get('chatbot_id')}"):
                        st.session_state.selected_chatbot = bot.get('chatbot_id')
                        st.session_state.current_view = 'chat'
                        st.rerun()
                
                if bot.get('embed_code'):
                    st.code(bot.get('embed_code'), language='html')
                    if st.button(f"📋 Copy Embed Code", key=f"copy_{bot.get('chatbot_id')}"):
                        st.success("✅ Embed code copied to clipboard!")
    else:
        st.info("No chatbots created yet. Use the form above to create your first chatbot!")

# Chat Interface View
def show_chat_interface():
    if not st.session_state.selected_chatbot:
        st.warning("⚠️ Please select a chatbot first")
        if st.button("← Back to Dashboard"):
            st.session_state.current_view = 'dashboard'
            st.rerun()
        return
    
    # Get chatbot details
    chatbot_data = api_request(f'chatbot/{st.session_state.selected_chatbot}')
    
    if not chatbot_data or not chatbot_data.get('success'):
        st.error("❌ Chatbot not found")
        return
    
    chatbot = chatbot_data.get('chatbot')
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f'<div class="main-header"><h1>💬 {chatbot.get("company_name")}</h1><p>AI-Powered Customer Support</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.metric("Questions", st.session_state.question_count)
    
    with col3:
        if st.session_state.lead_captured:
            st.success("✅ Lead Captured")
        else:
            st.info("🎯 Chatting...")
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    chat_placeholder = st.container()
    
    with chat_placeholder:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lead capture form (after 3 questions)
    if st.session_state.question_count >= 3 and not st.session_state.lead_captured:
        st.markdown("---")
        st.subheader("🎯 Quick Contact Information")
        st.write("We'd love to help you further! Please share your details:")
        
        with st.form("lead_capture_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("👤 Name", placeholder="John Doe")
                email = st.text_input("📧 Email", placeholder="john@example.com")
            
            with col2:
                phone = st.text_input("📱 Phone", placeholder="+1234567890")
                company = st.text_input("🏢 Company (Optional)", placeholder="Your Company")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("✅ Submit", use_container_width=True)
            with col_b:
                skipped = st.form_submit_button("⏭️ Skip", use_container_width=True)
            
            if submitted or skipped:
                lead_data = {
                    'chatbot_id': st.session_state.selected_chatbot,
                    'company_name': chatbot.get('company_name'),
                    'username': name if submitted else 'Anonymous',
                    'email': email if submitted else 'not_provided@example.com',
                    'phone': phone if submitted else 'Not provided',
                    'session_id': st.session_state.session_id,
                    'questions_asked': st.session_state.question_count,
                    'conversation': st.session_state.chat_history,
                    'timestart': st.session_state.conversation_start or datetime.now().isoformat()
                }
                
                result = api_request('lead/capture', method='POST', data=lead_data)
                
                if result and result.get('success'):
                    st.session_state.lead_captured = True
                    st.success("✅ Thank you! We'll get back to you soon.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
    
    # Chat input
    st.markdown("---")
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input("💬 Type your message...", key="chat_input", placeholder="Ask me anything about our services...")
    
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)
    
    if (send_button or user_input) and user_input:
        # Add user message
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # Set conversation start time
        if not st.session_state.conversation_start:
            st.session_state.conversation_start = datetime.now().isoformat()
        
        # Get bot response
        with st.spinner("🤖 Thinking..."):
            response_data = api_request('chat', method='POST', data={
                'chatbot_id': st.session_state.selected_chatbot,
                'message': user_input
            })
            
            if response_data and response_data.get('success'):
                bot_response = response_data.get('response')
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': bot_response,
                    'timestamp': datetime.now().isoformat()
                })
                st.session_state.question_count += 1
        
        st.rerun()
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.session_state.chat_history = []
        st.session_state.question_count = 0
        st.session_state.lead_captured = False
        st.session_state.conversation_start = None
        st.rerun()

# Leads View
def show_leads():
    st.markdown('<div class="main-header"><h1>📊 Lead Management</h1><p>View and manage captured leads</p></div>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chatbots = get_all_chatbots()
        chatbot_options = ['All Chatbots'] + [bot.get('company_name') for bot in chatbots]
        selected_bot = st.selectbox("🤖 Filter by Chatbot", chatbot_options)
    
    with col2:
        st.date_input("📅 From Date")
    
    with col3:
        st.date_input("📅 To Date")
    
    st.markdown("---")
    
    # Fetch leads
    leads_data = api_request('leads')
    
    if leads_data and leads_data.get('success'):
        leads = leads_data.get('leads', [])
        
        if leads:
            # Stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Total Leads", len(leads))
            
            with col2:
                valid_emails = len([l for l in leads if l.get('mailid') and '@' in l.get('mailid')])
                st.metric("✅ Valid Emails", valid_emails)
            
            with col3:
                avg_questions = sum(l.get('questions_asked', 0) for l in leads) / len(leads) if leads else 0
                st.metric("💬 Avg. Questions", f"{avg_questions:.1f}")
            
            st.markdown("---")
            
            # Leads table
            for lead in leads:
                with st.expander(f"🎯 {lead.get('username')} - {lead.get('company_name')} ({lead.get('timestart', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Name:** {lead.get('username')}")
                        st.write(f"**📧 Email:** {lead.get('mailid')}")
                        st.write(f"**📱 Phone:** {lead.get('phonenumber')}")
                    
                    with col2:
                        st.write(f"**🏢 Company:** {lead.get('company_name')}")
                        st.write(f"**💬 Questions:** {lead.get('questions_asked')}")
                        st.write(f"**🆔 Session:** {lead.get('session_id')}")
                    
                    # Conversation
                    if lead.get('conversation'):
                        st.subheader("💬 Conversation")
                        try:
                            conversation = json.loads(lead.get('conversation')) if isinstance(lead.get('conversation'), str) else lead.get('conversation')
                            
                            for msg in conversation:
                                if msg['role'] == 'user':
                                    st.markdown(f"**👤 User:** {msg['content']}")
                                else:
                                    st.markdown(f"**🤖 Bot:** {msg['content']}")
                        except:
                            st.write(lead.get('conversation'))
        else:
            st.info("📭 No leads captured yet. Start chatting to generate leads!")
    else:
        st.error("❌ Unable to fetch leads")

# Helper function to get all chatbots
def get_all_chatbots():
    chatbots_data = api_request('chatbots')
    if chatbots_data and chatbots_data.get('success'):
        return chatbots_data.get('chatbots', [])
    return []

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🎯 Navigation")
    
    if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    if st.button("🤖 Chatbots", use_container_width=True, key="nav_chatbots"):
        st.session_state.current_view = 'chatbots'
        st.rerun()
    
    if st.button("📋 Leads", use_container_width=True, key="nav_leads"):
        st.session_state.current_view = 'leads'
        st.rerun()
    
    if st.button("💬 Chat Test", use_container_width=True, key="nav_chat"):
        chatbots = get_all_chatbots()
        if chatbots:
            st.session_state.selected_chatbot = chatbots[0].get('chatbot_id')
            st.session_state.current_view = 'chat'
            st.rerun()
        else:
            st.warning("Create a chatbot first!")
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    st.markdown(f"**API Status:** {'🟢 Connected' if api_request('health') else '🔴 Disconnected'}")
    st.markdown(f"**Session:** {st.session_state.session_id}")
    
    st.markdown("---")
    st.markdown("### 📚 Resources")
    st.markdown("- [Documentation](#)")
    st.markdown("- [API Reference](#)")
    st.markdown("- [Support](#)")

# Main content based on current view
if st.session_state.current_view == 'dashboard':
    show_dashboard()
elif st.session_state.current_view == 'chatbots':
    show_chatbot_management()
elif st.session_state.current_view == 'chat':
    show_chat_interface()
elif st.session_state.current_view == 'leads':
    show_leads()
