"""
AI Medical Scheduling Agent - Chatbot Interface
Main Streamlit application with conversational AI interface
"""

import streamlit as st
import pandas as pd
import datetime
import os
from src.agent import MedicalSchedulingAgent, ConversationState
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
    .main-header {
        font-size: 2.5rem;
        color: #2c5aa0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2c5aa0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #1976d2;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #7b1fa2;
    }
    .success-message {
        background-color: #e8f5e8;
        border-left-color: #4caf50;
        color: #2e7d32;
    }
    .error-message {
        background-color: #ffebee;
        border-left-color: #f44336;
        color: #c62828;
    }
    .stButton > button {
        background-color: #2c5aa0;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #1e3d72;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = MedicalSchedulingAgent()
    
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
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        css_class = f"chat-message assistant-message {message_type}-message" if message_type != "normal" else "chat-message assistant-message"
        st.markdown(f"""
        <div class="{css_class}">
            <strong>AI Assistant:</strong> {message}
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

def process_user_input(user_input: str):
    """Process user input through the AI agent"""
    if not user_input.strip():
        return
    
    # Add user message to chat history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.datetime.now()
    })
    
    # Process through AI agent
    try:
        response = st.session_state.agent.process_message(user_input)
        
        # Determine message type based on conversation state
        message_type = "normal"
        if st.session_state.agent.conversation_state == ConversationState.COMPLETED:
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
        if st.session_state.agent.conversation_state == ConversationState.COMPLETED:
            st.session_state.current_appointment = st.session_state.agent.current_appointment
            
    except Exception as e:
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
        st.header("🔧 Admin Panel")
        
        if st.button("📊 Generate Reports"):
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
        
        if st.button("📅 Export Today's Schedule"):
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
        
        if st.button("🔄 Reset Conversation"):
            st.session_state.agent.reset_conversation()
            st.session_state.chat_history = []
            st.session_state.current_appointment = None
            st.success("✅ Conversation reset!")
            st.rerun()
        
        # Display current conversation state
        st.header("📋 Current Status")
        st.info(f"**State:** {st.session_state.agent.conversation_state.value}")
        
        if st.session_state.agent.current_patient.first_name:
            st.info(f"**Patient:** {st.session_state.agent.current_patient.first_name}")
        
        if st.session_state.agent.current_appointment:
            st.info(f"**Doctor:** {st.session_state.agent.current_appointment.doctor}")
            st.info(f"**Date:** {st.session_state.agent.current_appointment.date}")
            st.info(f"**Time:** {st.session_state.agent.current_appointment.time}")
        
        # Quick stats
        st.header("📈 Quick Stats")
        try:
            patients_df = pd.read_csv("data/patients.csv")
            appointments_df = pd.read_excel("data/appointments.xlsx")
            
            st.metric("Total Patients", len(patients_df))
            st.metric("Total Appointments", len(appointments_df))
            st.metric("New Patients", len(patients_df[patients_df['PatientType'] == 'New']))
            st.metric("Returning Patients", len(patients_df[patients_df['PatientType'] == 'Returning']))
            
        except Exception as e:
            st.warning("Could not load statistics")
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Chat with AI Assistant")
        
        # Display chat history
        if st.session_state.chat_history:
            display_chat_history()
        else:
            st.info("👋 Hello! I'm your AI medical scheduling assistant. I can help you book appointments, check availability, and manage your medical visits. How can I assist you today?")
        
        # Chat input
        user_input = st.text_input(
            "Type your message here...",
            placeholder="e.g., Hi, I'd like to book an appointment",
            key="chat_input"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("Send", type="primary"):
                process_user_input(user_input)
                st.rerun()
        
        with col_btn2:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col_btn3:
            if st.button("Help"):
                help_message = """
                **How to use this AI assistant:**
                
                1. **Start by greeting** - Say hello or mention you want to book an appointment
                2. **Provide your name** - The assistant will ask for your first name
                3. **Give your date of birth** - Use MM/DD/YYYY format
                4. **Choose a doctor** - Select from available doctors
                5. **Pick a time slot** - Choose from available appointment times
                6. **Provide insurance info** - Share your insurance details
                7. **Confirm appointment** - Review and confirm your booking
                
                **Example conversation:**
                - "Hi, I'd like to book an appointment"
                - "My name is John"
                - "My DOB is 01/15/1990"
                - "I'd like to see Dr. Smith"
                - "I'll take slot 2"
                - "My insurance is Blue Cross, member ID is ABC123"
                """
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': help_message,
                    'type': 'normal',
                    'timestamp': datetime.datetime.now()
                })
                st.rerun()
    
    with col2:
        st.header("📋 Appointment Details")
        
        if st.session_state.current_appointment:
            appointment = st.session_state.current_appointment
            patient = appointment.patient
            
            st.success("✅ Appointment Confirmed!")
            
            st.subheader("Patient Info")
            st.write(f"**Name:** {patient.first_name} {patient.last_name}")
            st.write(f"**Type:** {patient.patient_type}")
            st.write(f"**Email:** {patient.email}")
            st.write(f"**Phone:** {patient.phone}")
            
            st.subheader("Appointment Info")
            st.write(f"**Doctor:** {appointment.doctor}")
            st.write(f"**Date:** {appointment.date}")
            st.write(f"**Time:** {appointment.time}")
            st.write(f"**Duration:** {appointment.duration} minutes")
            
            if appointment.insurance:
                st.subheader("Insurance Info")
                st.write(f"**Carrier:** {appointment.insurance.carrier}")
                st.write(f"**Member ID:** {appointment.insurance.member_id}")
                st.write(f"**Group:** {appointment.insurance.group_number}")
            
            # Action buttons
            if st.button("📧 Send Intake Form"):
                try:
                    result = send_intake_form(patient.email)
                    st.success(result)
                except Exception as e:
                    st.error(f"Failed to send intake form: {str(e)}")
            
            if st.button("📅 Schedule Reminders"):
                try:
                    appointment_details = {
                        'patient_name': f"{patient.first_name} {patient.last_name}",
                        'patient_email': patient.email,
                        'patient_phone': patient.phone,
                        'patient_id': patient.patient_id,
                        'doctor': appointment.doctor,
                        'date': appointment.date,
                        'time': appointment.time,
                        'duration': appointment.duration
                    }
                    reminder_system.schedule_reminders(appointment_details)
                    st.success("✅ Reminders scheduled!")
                except Exception as e:
                    st.error(f"Failed to schedule reminders: {str(e)}")
        
        else:
            st.info("No appointment details available. Start a conversation to book an appointment!")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("👥 View All Patients"):
            try:
                patients_df = pd.read_csv("data/patients.csv")
                st.dataframe(patients_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load patients: {str(e)}")
        
        if st.button("📅 View All Appointments"):
            try:
                appointments_df = pd.read_excel("data/appointments.xlsx")
                st.dataframe(appointments_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load appointments: {str(e)}")
        
        if st.button("🏥 View Doctor Schedules"):
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
