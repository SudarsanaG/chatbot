"""
AI Medical Scheduling Agent - Chatbot Interface
Main Streamlit application with conversational AI interface
"""

import streamlit as st
import pandas as pd
import datetime
import os
from src.multi_agent_system import MultiAgentMedicalSchedulingSystem
from src.agent import ConversationState
from src.data_generator import MedicalDataGenerator
from src.reminder_system import reminder_system
from src.excel_export import excel_exporter
from src.utils import send_intake_form

# Page configuration
st.set_page_config(
    page_title="RagaAI Medical Scheduling Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        color: #1a365d;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Chat message containers */
    .chat-message {
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border-left: 5px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.5;
    }
    
    /* User messages */
    .user-message {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        color: white;
        border-left-color: #2d3748;
        margin-left: 20%;
        text-align: right;
    }
    
    /* Assistant messages */
    .assistant-message {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        color: white;
        border-left-color: #1a202c;
        margin-right: 20%;
        text-align: left;
    }
    
    /* Success messages */
    .success-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border-left-color: #00bcd4;
        font-weight: bold;
    }
    
    /* Error messages */
    .error-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        border-left-color: #f44336;
        font-weight: bold;
    }
    
    /* Loading messages */
    .loading-message {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: white;
        border-left-color: #4a5568;
        font-style: italic;
    }
    
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots::after {
        content: '';
        animation: dots 1.5s steps(4, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.8rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5a6fd8;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = MultiAgentMedicalSchedulingSystem()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_appointment' not in st.session_state:
        st.session_state.current_appointment = None
    
    if 'data_initialized' not in st.session_state:
        st.session_state.data_initialized = False

def initialize_data():
    """Initialize synthetic data if not already done"""
    if not st.session_state.data_initialized:
        try:
            # Check if data files exist
            if not os.path.exists("data/patients.csv") or not os.path.exists("data/schedules.xlsx"):
                with st.spinner("Initializing synthetic data..."):
                    generator = MedicalDataGenerator()
                    generator.create_data_files()
            
            st.session_state.data_initialized = True
            st.success("✅ Data initialized successfully!")
            
        except Exception as e:
            st.error(f"❌ Failed to initialize data: {str(e)}")

def display_chat_message(message: str, is_user: bool = False, message_type: str = "normal"):
    """Display a chat message with appropriate styling"""
    # Clean the message of any HTML tags that might have leaked in
    import re
    clean_message = re.sub(r'<[^>]+>', '', message)
    # Also clean any remaining HTML entities and extra whitespace
    clean_message = clean_message.replace('&nbsp;', ' ').strip()
    
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {clean_message}
        </div>
        """, unsafe_allow_html=True)
    else:
        if message_type == "loading":
            css_class = "chat-message loading-message"
            st.markdown(f"""
            <div class="{css_class}">
                <strong>AI Assistant:</strong> {clean_message}
            </div>
            """, unsafe_allow_html=True)
        else:
            css_class = f"chat-message assistant-message {message_type}-message" if message_type != "normal" else "chat-message assistant-message"
            st.markdown(f"""
            <div class="{css_class}">
                <strong>AI Assistant:</strong> {clean_message}
            </div>
            """, unsafe_allow_html=True)

def display_chat_history():
    """Display the chat history"""
    for message in st.session_state.chat_history:
        display_chat_message(
            message['content'], 
            is_user=message['role'] == 'user',
            message_type=message.get('type', 'normal')
        )

def display_selection_buttons():
    """Display selection buttons for doctor and slot selection"""
    current_state = st.session_state.agent.get_conversation_state()
    
    if current_state == "doctor_selection":
        display_doctor_selection_buttons()
    elif current_state == "scheduling":
        display_slot_selection_buttons()

def display_doctor_selection_buttons():
    """Display doctor selection buttons"""
    st.markdown("### 👨‍⚕️ Select Your Doctor")
    
    # Get available doctors from the system
    try:
        # Load doctors from schedule database
        schedules_df = pd.read_excel("data/schedules.xlsx")
        available_doctors = list(schedules_df['Doctor'].unique())
        
        # Create columns for doctor buttons
        cols = st.columns(2)
        
        for i, doctor in enumerate(available_doctors):
            col_idx = i % 2
            with cols[col_idx]:
                # Clean doctor name
                doctor_name = doctor.replace("Dr. ", "").replace("Dr ", "")
                
                if st.button(
                    f"👨‍⚕️ Dr. {doctor_name}",
                    key=f"doctor_{i}",
                    use_container_width=True,
                    help=f"Select Dr. {doctor_name}"
                ):
                    # Process doctor selection
                    process_doctor_selection(doctor)
                    
    except Exception as e:
        st.error(f"Error loading doctors: {str(e)}")

def display_slot_selection_buttons():
    """Display appointment slot selection buttons"""
    st.markdown("### 📅 Select Your Appointment Time")
    
    # Get selected doctor from session state
    appointment_info = st.session_state.agent.get_appointment_info()
    if not appointment_info or not appointment_info.get('doctor'):
        st.error("No doctor selected. Please select a doctor first.")
        return
    
    selected_doctor = appointment_info['doctor']
    
    try:
        # Load available slots for the selected doctor
        schedules_df = pd.read_excel("data/schedules.xlsx")
        available_slots = schedules_df[
            (schedules_df["Doctor"] == selected_doctor) & 
            (schedules_df["Available"] == "Yes")
        ]
        
        if available_slots.empty:
            st.warning(f"No available slots for {selected_doctor}")
            return
        
        # Group slots by date
        slots_by_date = {}
        for _, slot in available_slots.iterrows():
            date = slot['Date']
            time = slot['Time']
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(time)
        
        # Display slots by date
        for date, times in sorted(slots_by_date.items()):
            st.markdown(f"**📅 {date}**")
            
            # Create columns for time slots
            time_cols = st.columns(min(len(times), 4))
            
            for i, time in enumerate(sorted(times)):
                col_idx = i % 4
                with time_cols[col_idx]:
                    # Get patient type to determine duration
                    patient_info = st.session_state.agent.get_patient_info()
                    duration = 60 if patient_info.get('patient_type') == 'New' else 30
                    
                    if st.button(
                        f"🕐 {time}\n({duration}min)",
                        key=f"slot_{date}_{time}",
                        use_container_width=True,
                        help=f"Book {duration}-minute appointment on {date} at {time}"
                    ):
                        # Process slot selection
                        process_slot_selection(selected_doctor, date, time)
                        
    except Exception as e:
        st.error(f"Error loading slots: {str(e)}")

def process_doctor_selection(doctor):
    """Process doctor selection"""
    try:
        # Add user message to chat
        st.session_state.chat_history.append({
            'role': 'user',
            'content': f"Select {doctor}",
            'type': 'normal',
            'timestamp': datetime.datetime.now()
        })
        
        # Process through the agent
        response = st.session_state.agent.process_message(f"Select {doctor}")
        
        # Add assistant response
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'type': 'normal',
            'timestamp': datetime.datetime.now()
        })
        
        # Force rerun to update the UI
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing doctor selection: {str(e)}")

def process_slot_selection(doctor, date, time):
    """Process slot selection"""
    try:
        # Add user message to chat
        st.session_state.chat_history.append({
            'role': 'user',
            'content': f"Book appointment with {doctor} on {date} at {time}",
            'type': 'normal',
            'timestamp': datetime.datetime.now()
        })
        
        # Process through the agent
        response = st.session_state.agent.process_message(f"Book appointment with {doctor} on {date} at {time}")
        
        # Add assistant response
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'type': 'normal',
            'timestamp': datetime.datetime.now()
        })
        
        # Force rerun to update the UI
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing slot selection: {str(e)}")

def process_user_input(user_input: str):
    """Process user input through the AI agent"""
    if not user_input.strip():
        return
    
    # Add user message to chat history immediately
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.datetime.now()
    })
    
    # Create a placeholder for the AI response
    response_placeholder = st.empty()
    
    # Show loading indicator
    with response_placeholder.container():
        st.markdown("""
        <div class="chat-message loading-message">
            <strong>AI Assistant:</strong> 🤖 Thinking<span class="loading-dots"></span>
        </div>
        """, unsafe_allow_html=True)
    
    # Process through AI agent
    try:
        response = st.session_state.agent.process_message(user_input)
        
        # Clear the loading indicator
        response_placeholder.empty()
        
        # Determine message type based on conversation state
        message_type = "normal"
        current_state = st.session_state.agent.get_conversation_state()
        if current_state == "completed":
            message_type = "success"
        elif "error" in response.lower() or "sorry" in response.lower():
            message_type = "error"
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'type': message_type,
            'timestamp': datetime.datetime.now()
        })
        
        # If appointment is completed, store it
        if current_state == "completed":
            st.session_state.current_appointment = st.session_state.agent.get_appointment_info()
            
    except Exception as e:
        # Clear the loading indicator
        response_placeholder.empty()
        
        error_message = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': error_message,
            'type': 'error',
            'timestamp': datetime.datetime.now()
        })

def main():
    """Main application function"""
    initialize_session_state()
    initialize_data()
    
    # Header
    st.markdown('<h1 class="main-header">🏥 RagaAI Medical Scheduling Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar for admin functions
    with st.sidebar:
        st.markdown("### 🔧 Admin Panel")
        st.markdown("---")
        
        # Admin buttons with better styling
        if st.button("📊 Generate Reports", use_container_width=True):
            with st.spinner("Generating reports..."):
                try:
                    # Generate appointments report
                    appointments_report = excel_exporter.export_appointments_report()
                    
                    # Generate patient database export
                    patient_db = excel_exporter.export_patient_database()
                    
                    # Generate revenue report
                    revenue_report = excel_exporter.export_revenue_report()
                    
                    st.success("✅ Reports generated successfully!")
                    st.info("Check the 'exports' folder for generated files.")
                    
                except Exception as e:
                    st.error(f"❌ Failed to generate reports: {str(e)}")
        
        if st.button("📅 Export Today's Schedule", use_container_width=True):
            today = datetime.date.today().strftime("%Y-%m-%d")
            with st.spinner("Exporting today's schedule..."):
                try:
                    daily_schedule = excel_exporter.export_daily_schedule(today)
                    if daily_schedule:
                        st.success(f"✅ Today's schedule exported!")
                    else:
                        st.warning("No schedule data found for today.")
                except Exception as e:
                    st.error(f"❌ Failed to export schedule: {str(e)}")
        
        st.markdown("---")
        
        # Display current conversation state with better styling
        st.markdown("### 📋 Current Status")
        
        # Status card
        current_state = st.session_state.agent.get_conversation_state()
        state_colors = {
            "greeting": "🟢",
            "collecting_info": "🟡", 
            "patient_lookup": "🔵",
            "new_patient_registration": "🟠",
            "doctor_selection": "🟣",
            "scheduling": "🔴",
            "insurance_collection": "🟤",
            "confirmation": "✅",
            "completed": "🎉"
        }
        
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0.5rem 0;">
            <strong>{state_colors.get(current_state, "⚪")} State:</strong><br>
            <span style="color: #666; text-transform: capitalize;">{current_state.replace('_', ' ')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        patient_info = st.session_state.agent.get_patient_info()
        if patient_info.get("first_name"):
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0.5rem 0;">
                <strong>👤 Patient:</strong><br>
                <span style="color: #666;">{patient_info['first_name']} {patient_info.get('last_name', '')}</span>
            </div>
            """, unsafe_allow_html=True)
        
        appointment_info = st.session_state.agent.get_appointment_info()
        if appointment_info:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0.5rem 0;">
                <strong>👨‍⚕️ Doctor:</strong> {appointment_info.get('doctor', 'N/A')}<br>
                <strong>📅 Date:</strong> {appointment_info.get('date', 'N/A')}<br>
                <strong>⏰ Time:</strong> {appointment_info.get('time', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick stats with better styling
        st.markdown("### 📈 Quick Stats")
        try:
            patients_df = pd.read_csv("data/patients.csv")
            appointments_df = pd.read_excel("data/appointments.xlsx")
            
            # Create metrics with better styling
            col1, col2 = st.columns(2)
            with col1:
                st.metric("👥 Total Patients", len(patients_df))
                st.metric("🆕 New Patients", len(patients_df[patients_df['PatientType'] == 'New']))
            with col2:
                st.metric("📅 Total Appointments", len(appointments_df))
                st.metric("🔄 Returning Patients", len(patients_df[patients_df['PatientType'] == 'Returning']))
            
        except Exception as e:
            st.warning("Could not load statistics")
        
        st.markdown("---")
        
        # System info
        st.markdown("### 🤖 System Info")
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0.5rem 0;">
            <strong>🧠 AI Provider:</strong> Gemini 2.0 Flash<br>
            <strong>🏗️ Architecture:</strong> Multi-Agent System<br>
            <strong>⚡ Status:</strong> <span style="color: green;">Active</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Chat with AI Assistant")
        st.markdown("---")
        
        # Chat container with better styling
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            if st.session_state.chat_history:
                display_chat_history()
            else:
                st.markdown("""
                <div class="chat-message assistant-message">
                    <strong>👋 Welcome!</strong><br><br>
                    I'm your AI medical scheduling assistant powered by <strong>Gemini 2.0 Flash</strong> and a <strong>multi-agent system</strong>!<br><br>
                    I can help you:<br>
                    • 📅 Book appointments<br>
                    • 👨‍⚕️ Choose doctors<br>
                    • 📋 Manage your information<br>
                    • 💳 Handle insurance details<br><br>
                    <em>How can I assist you today?</em>
                </div>
                """, unsafe_allow_html=True)
            
            # Add button-based selection interface
            display_selection_buttons()
        
        # Chat input section
        st.markdown("---")
        st.markdown("### 💭 Your Message")
        
        # Use a form to handle Enter key properly
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Type your message here...",
                placeholder="e.g., Hi, I'd like to book an appointment",
                help="Type your message and press Enter or click Send"
            )
            
            # Button row with better spacing
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            
            with col_btn1:
                send_pressed = st.form_submit_button("📤 Send", type="primary", use_container_width=True)
            
            with col_btn2:
                clear_pressed = st.form_submit_button("🗑️ Clear", use_container_width=True)
            
            with col_btn3:
                help_pressed = st.form_submit_button("❓ Help", use_container_width=True)
            
            with col_btn4:
                reset_pressed = st.form_submit_button("🔄 Reset", use_container_width=True)
        
        # Handle form submissions
        if send_pressed:
            if user_input.strip():
                process_user_input(user_input)
                st.rerun()
            else:
                st.warning("Please enter a message first!")
        
        if clear_pressed:
            st.session_state.chat_history = []
            st.rerun()
        
        if help_pressed:
            help_message = """
            **🤖 Multi-Agent AI Assistant Guide**
            
            **Our specialized agents will help you:**
            
            🔍 **Information Collector** - Gathers your personal details
            👤 **Patient Manager** - Handles your registration and lookup
            📅 **Scheduler** - Manages doctor selection and appointments
            💳 **Insurance Handler** - Processes your insurance information
            ✅ **Confirmation Agent** - Finalizes your appointment
            
            **📝 Sample Conversation:**
            1. "Hi, I'd like to book an appointment"
            2. "My name is John Smith"
            3. "My DOB is 01/15/1990"
            4. "My phone is 555-123-4567"
            5. "My email is john@email.com"
            6. "I'd like to see Dr. Johnson"
            7. "I'll take slot 1"
            8. "My insurance is Blue Cross, member ID ABC123"
            
            **💡 Tips:**
            • Be natural - I understand conversational language
            • Provide information as it comes to mind
            • I'll guide you through each step
            • All your data is secure and private
            • Ask "What's my name?" to check your information
            """
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': help_message,
                'type': 'normal',
                'timestamp': datetime.datetime.now()
            })
            st.rerun()
        
        if reset_pressed:
            st.session_state.agent.reset_conversation()
            st.session_state.chat_history = []
            st.session_state.current_appointment = None
            st.success("✅ Conversation reset!")
            st.rerun()
    
    with col2:
        st.markdown("### 📋 Appointment Details")
        st.markdown("---")
        
        if st.session_state.current_appointment:
            appointment = st.session_state.current_appointment
            patient_info = st.session_state.agent.get_patient_info()
            
            # Success banner
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: white;">✅ Appointment Confirmed!</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Patient info card
            st.markdown("#### 👤 Patient Information")
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem;">
                <strong>Name:</strong> {patient_info.get('first_name', 'N/A')} {patient_info.get('last_name', 'N/A')}<br>
                <strong>Type:</strong> {patient_info.get('patient_type', 'N/A')} Patient<br>
                <strong>Email:</strong> {patient_info.get('email', 'N/A')}<br>
                <strong>Phone:</strong> {patient_info.get('phone', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            # Appointment info card
            st.markdown("#### 📅 Appointment Information")
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem;">
                <strong>👨‍⚕️ Doctor:</strong> {appointment.get('doctor', 'N/A')}<br>
                <strong>📅 Date:</strong> {appointment.get('date', 'N/A')}<br>
                <strong>⏰ Time:</strong> {appointment.get('time', 'N/A')}<br>
                <strong>⏱️ Duration:</strong> {appointment.get('duration', 'N/A')} minutes
            </div>
            """, unsafe_allow_html=True)
            
            # Insurance info card
            insurance_info = appointment.get('insurance')
            if insurance_info:
                st.markdown("#### 💳 Insurance Information")
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem;">
                    <strong>Carrier:</strong> {insurance_info.get('carrier', 'N/A')}<br>
                    <strong>Member ID:</strong> {insurance_info.get('member_id', 'N/A')}<br>
                    <strong>Group:</strong> {insurance_info.get('group_number', 'N/A')}
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("#### ⚡ Actions")
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                if st.button("📧 Send Form", use_container_width=True):
                    try:
                        result = send_intake_form(patient_info.get('email', ''))
                        st.success(result)
                    except Exception as e:
                        st.error(f"Failed to send intake form: {str(e)}")
            
            with col_act2:
                if st.button("📅 Reminders", use_container_width=True):
                    try:
                        appointment_details = {
                            'patient_name': f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}",
                            'patient_email': patient_info.get('email', ''),
                            'patient_phone': patient_info.get('phone', ''),
                            'patient_id': patient_info.get('patient_id', ''),
                            'doctor': appointment.get('doctor', ''),
                            'date': appointment.get('date', ''),
                            'time': appointment.get('time', ''),
                            'duration': appointment.get('duration', 30)
                        }
                        reminder_system.schedule_reminders(appointment_details)
                        st.success("✅ Reminders scheduled!")
                    except Exception as e:
                        st.error(f"Failed to schedule reminders: {str(e)}")
        
        else:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center; border: 2px dashed #dee2e6;">
                <h4 style="color: #6c757d; margin-bottom: 1rem;">📋 No Appointment Details</h4>
                <p style="color: #6c757d; margin: 0;">Start a conversation to book an appointment!</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick actions with better styling
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("👥 View All Patients", use_container_width=True):
            try:
                patients_df = pd.read_csv("data/patients.csv")
                st.dataframe(patients_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load patients: {str(e)}")
        
        if st.button("📅 View All Appointments", use_container_width=True):
            try:
                appointments_df = pd.read_excel("data/appointments.xlsx")
                st.dataframe(appointments_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load appointments: {str(e)}")
        
        if st.button("🏥 View Doctor Schedules", use_container_width=True):
            try:
                # Try original file first, then new file if locked
                try:
                    schedules_df = pd.read_excel("data/schedules.xlsx")
                except PermissionError:
                    schedules_df = pd.read_excel("data/schedules_new.xlsx")
                st.dataframe(schedules_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load schedules: {str(e)}")

if __name__ == "__main__":
    main()
