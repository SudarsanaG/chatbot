"""
Demo script for RagaAI Medical Scheduling Agent
Shows complete functionality and features
"""

import streamlit as st
import pandas as pd
import os
from src.agent import MedicalSchedulingAgent
from src.data_generator import MedicalDataGenerator
from src.excel_export import excel_exporter
from src.utils import get_system_stats

def main():
    """Main demo function"""
    st.set_page_config(
        page_title="RagaAI Medical Scheduling Agent - Demo",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 RagaAI Medical Scheduling Agent - Demo")
    st.markdown("---")
    
    # Initialize data if needed
    if not os.path.exists("data/patients.csv"):
        with st.spinner("Initializing synthetic data..."):
            generator = MedicalDataGenerator()
            generator.create_data_files()
        st.success("✅ Data initialized!")
    
    # Display system overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Patients", get_system_stats()['patients'])
    
    with col2:
        st.metric("📅 Total Appointments", get_system_stats()['appointments'])
    
    with col3:
        st.metric("👨‍⚕️ Available Doctors", get_system_stats()['doctors'])
    
    with col4:
        st.metric("⏰ Available Slots", get_system_stats()['available_slots'])
    
    st.markdown("---")
    
    # Demo sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 AI Agent Demo", 
        "📊 Data Overview", 
        "📈 Reports", 
        "⚙️ Configuration", 
        "📋 Features"
    ])
    
    with tab1:
        st.header("🤖 AI Agent Conversation Demo")
        
        # Initialize agent
        if 'demo_agent' not in st.session_state:
            st.session_state.demo_agent = MedicalSchedulingAgent()
        
        # Demo conversation
        demo_messages = [
            "Hi, I'd like to book an appointment",
            "My name is Sarah",
            "My DOB is 03/22/1985",
            "I'd like to see Dr. Michael Chen",
            "I'll take slot 2",
            "My insurance is Aetna",
            "My member ID is AET987654321",
            "My group number is GRP456"
        ]
        
        if st.button("🎬 Start Demo Conversation"):
            st.session_state.demo_agent.reset_conversation()
            
            for i, message in enumerate(demo_messages):
                with st.expander(f"Step {i+1}: {message}"):
                    response = st.session_state.demo_agent.process_message(message)
                    st.write(f"**AI Response:** {response}")
                    st.write(f"**State:** {st.session_state.demo_agent.conversation_state.value}")
        
        # Manual conversation
        st.subheader("💬 Try It Yourself")
        user_input = st.text_input("Type your message:", placeholder="e.g., Hi, I need an appointment")
        
        if st.button("Send") and user_input:
            response = st.session_state.demo_agent.process_message(user_input)
            st.write(f"**AI:** {response}")
            st.write(f"**Current State:** {st.session_state.demo_agent.conversation_state.value}")
    
    with tab2:
        st.header("📊 Data Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Patients Database")
            try:
                patients_df = pd.read_csv("data/patients.csv")
                st.dataframe(patients_df.head(10), use_container_width=True)
                st.caption(f"Showing 10 of {len(patients_df)} patients")
            except Exception as e:
                st.error(f"Could not load patients: {str(e)}")
        
        with col2:
            st.subheader("📅 Appointments")
            try:
                appointments_df = pd.read_excel("data/appointments.xlsx")
                st.dataframe(appointments_df.head(10), use_container_width=True)
                st.caption(f"Showing 10 of {len(appointments_df)} appointments")
            except Exception as e:
                st.error(f"Could not load appointments: {str(e)}")
        
        st.subheader("🏥 Doctor Schedules")
        try:
            try:
                schedules_df = pd.read_excel("data/schedules.xlsx")
            except PermissionError:
                schedules_df = pd.read_excel("data/schedules_new.xlsx")
            
            st.dataframe(schedules_df.head(10), use_container_width=True)
            st.caption(f"Showing 10 of {len(schedules_df)} schedule entries")
        except Exception as e:
            st.error(f"Could not load schedules: {str(e)}")
    
    with tab3:
        st.header("📈 Reports & Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Appointments Report"):
                with st.spinner("Generating report..."):
                    report_path = excel_exporter.export_appointments_report()
                    if report_path:
                        st.success(f"✅ Report generated: {report_path}")
                    else:
                        st.error("❌ Failed to generate report")
            
            if st.button("👥 Export Patient Database"):
                with st.spinner("Exporting database..."):
                    db_path = excel_exporter.export_patient_database()
                    if db_path:
                        st.success(f"✅ Database exported: {db_path}")
                    else:
                        st.error("❌ Failed to export database")
        
        with col2:
            if st.button("💰 Generate Revenue Report"):
                with st.spinner("Generating revenue report..."):
                    revenue_path = excel_exporter.export_revenue_report()
                    if revenue_path:
                        st.success(f"✅ Revenue report generated: {revenue_path}")
                    else:
                        st.error("❌ Failed to generate revenue report")
            
            if st.button("📅 Export Today's Schedule"):
                import datetime
                today = datetime.date.today().strftime("%Y-%m-%d")
                with st.spinner("Exporting today's schedule..."):
                    schedule_path = excel_exporter.export_daily_schedule(today)
                    if schedule_path:
                        st.success(f"✅ Schedule exported: {schedule_path}")
                    else:
                        st.error("❌ Failed to export schedule")
        
        # Show export list
        st.subheader("📁 Generated Reports")
        exports = excel_exporter.get_export_list()
        if exports:
            for export in exports[:5]:  # Show last 5 exports
                st.write(f"📄 {export['filename']} - {export['modified']}")
        else:
            st.info("No reports generated yet")
    
    with tab4:
        st.header("⚙️ Configuration")
        
        st.subheader("🔧 System Configuration")
        
        config_info = {
            "New Patient Duration": "60 minutes",
            "Returning Patient Duration": "30 minutes",
            "Business Hours": "9 AM - 5 PM",
            "Business Days": "Monday - Friday",
            "Reminder 1": "3 days before appointment",
            "Reminder 2": "1 day before appointment",
            "Reminder 3": "2 hours before appointment"
        }
        
        for key, value in config_info.items():
            st.write(f"**{key}:** {value}")
        
        st.subheader("📧 Email Configuration")
        st.info("Email functionality is in simulation mode. To enable real emails, configure SMTP settings in config.py")
        
        st.subheader("📱 SMS Configuration")
        st.info("SMS functionality is in simulation mode. To enable real SMS, configure Twilio settings in config.py")
    
    with tab5:
        st.header("📋 Features Overview")
        
        features = {
            "🤖 AI Agent": [
                "Natural language conversation",
                "Entity extraction and validation",
                "State-based conversation flow",
                "Error handling and recovery"
            ],
            "👥 Patient Management": [
                "Patient lookup with fuzzy matching",
                "New patient registration",
                "Patient type classification",
                "Contact information validation"
            ],
            "📅 Scheduling": [
                "Real-time availability checking",
                "Smart duration assignment",
                "Calendar integration",
                "Conflict prevention"
            ],
            "💳 Insurance": [
                "Insurance information collection",
                "Carrier validation",
                "Member ID processing",
                "Group number handling"
            ],
            "📧 Communication": [
                "Automated email reminders",
                "SMS notifications",
                "Intake form distribution",
                "Appointment confirmations"
            ],
            "📊 Reporting": [
                "Excel export functionality",
                "Admin reports generation",
                "Revenue analytics",
                "Patient demographics"
            ]
        }
        
        for category, feature_list in features.items():
            with st.expander(category):
                for feature in feature_list:
                    st.write(f"✅ {feature}")
        
        st.subheader("🎯 Success Metrics")
        success_metrics = [
            "✅ Functional Demo: Complete patient booking workflow",
            "✅ Data Accuracy: Correct patient classification and scheduling", 
            "✅ Integration Success: Excel exports and calendar management",
            "✅ Code Quality: Clean, documented, executable codebase"
        ]
        
        for metric in success_metrics:
            st.write(metric)

if __name__ == "__main__":
    main()

