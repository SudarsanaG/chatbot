"""
Multi-Agent Coordinator
Orchestrates the interaction between different specialized agents
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from datetime import datetime

from src.gemini_client import GeminiClient
from src.information_collector_agent import InformationCollectorAgent, CollectionResult
from src.scheduling_agent import SchedulingAgent, SchedulingResult
from src.patient_management_agent import PatientManagementAgent, PatientLookupResult, RegistrationResult
from src.user_manager import UserManager
from src.agent import PatientInfo, AppointmentInfo, ConversationState, InsuranceInfo

class AgentType(Enum):
    """Types of agents in the system"""
    INFORMATION_COLLECTOR = "information_collector"
    PATIENT_MANAGER = "patient_manager"
    SCHEDULER = "scheduler"
    INSURANCE_HANDLER = "insurance_handler"
    CONFIRMATION_AGENT = "confirmation_agent"

@dataclass
class ConversationContext:
    """Context for the conversation"""
    current_state: ConversationState
    patient_info: PatientInfo
    appointment_info: Optional[AppointmentInfo]
    conversation_history: List[Dict[str, str]]
    available_doctors: List[str]
    available_slots: List[Dict[str, Any]]

@dataclass
class AgentResponse:
    """Response from an agent"""
    success: bool
    message: str
    next_state: ConversationState
    updated_context: ConversationContext
    agent_used: AgentType

class MultiAgentCoordinator:
    """Coordinates multiple specialized agents for medical scheduling"""
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize the multi-agent coordinator"""
        
        # Initialize Gemini client
        self.gemini = GeminiClient(gemini_api_key)
        
        # Load databases
        self.patients_db = self._load_patients_db()
        self.schedules_db = self._load_schedules_db()
        
        # Initialize specialized agents
        self.information_collector = InformationCollectorAgent(self.gemini)
        self.patient_manager = PatientManagementAgent(self.gemini, self.patients_db)
        self.scheduler = SchedulingAgent(self.gemini, self.schedules_db)
        self.user_manager = UserManager()
        
        # Initialize conversation context
        self.context = ConversationContext(
            current_state=ConversationState.GREETING,
            patient_info=PatientInfo(),
            appointment_info=None,
            conversation_history=[],
            available_doctors=list(self.schedules_db['Doctor'].unique()) if not self.schedules_db.empty else [],
            available_slots=[]
        )
    
    def _load_patients_db(self) -> pd.DataFrame:
        """Load patient database from CSV"""
        try:
            return pd.read_csv("data/patients.csv")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def _load_schedules_db(self) -> pd.DataFrame:
        """Load doctor schedules from Excel"""
        try:
            try:
                return pd.read_excel("data/schedules_new.xlsx")
            except (PermissionError, FileNotFoundError):
                return pd.read_excel("data/schedules.xlsx")
        except FileNotFoundError:
            return pd.DataFrame()
    
    def process_message(self, user_input: str) -> str:
        """Process user message through the appropriate agent"""
        
        # Add user message to conversation history
        self.context.conversation_history.append({"role": "user", "content": user_input})
        
        # Check if this is a context question first
        context_response = self._handle_context_question(user_input)
        if context_response:
            self.context.conversation_history.append({"role": "assistant", "content": context_response})
            return context_response
        
        # Determine which agent should handle this message
        agent_response = self._route_to_agent(user_input)
        
        # Update context with agent response
        self.context = agent_response.updated_context
        
        # Add assistant response to conversation history
        self.context.conversation_history.append({"role": "assistant", "content": agent_response.message})
        
        return agent_response.message
    
    def _handle_context_question(self, user_input: str) -> str:
        """Handle context questions like 'What's my name?'"""
        
        user_input_lower = user_input.lower().strip()
        patient_info = self.context.patient_info
        
        # Don't intercept simple responses like "ok", "yes", "sure", etc.
        simple_responses = ["ok", "okay", "yes", "yeah", "yep", "sure", "alright", "fine", "good", "great"]
        if user_input_lower in simple_responses:
            return None  # Let the normal flow handle these
        
        # Check for name questions
        if any(phrase in user_input_lower for phrase in ["what's my name", "what is my name", "my name", "who am i"]):
            if patient_info.first_name:
                return f"Your name is {patient_info.first_name} {patient_info.last_name if patient_info.last_name else ''}".strip()
            else:
                return "I don't have your name yet. Could you please tell me your name?"
        
        # Check for contact info questions
        if any(phrase in user_input_lower for phrase in ["my phone", "my number", "my email", "my contact"]):
            if patient_info.phone or patient_info.email:
                response = "Here's your contact information:\n"
                if patient_info.phone:
                    response += f"📞 Phone: {patient_info.phone}\n"
                if patient_info.email:
                    response += f"📧 Email: {patient_info.email}"
                return response.strip()
            else:
                return "I don't have your contact information yet. Could you please provide your phone number and email?"
        
        # Check for appointment questions
        if any(phrase in user_input_lower for phrase in ["my appointment", "appointment details", "when is my appointment"]):
            if self.context.appointment_info:
                appointment = self.context.appointment_info
                return f"Your appointment is scheduled with {appointment.doctor} on {appointment.date} at {appointment.time} for {appointment.duration} minutes."
            else:
                return "You don't have an appointment scheduled yet. Would you like to book one?"
        
        # Check for status questions
        if any(phrase in user_input_lower for phrase in ["where are we", "what's next", "current status", "what do you need"]):
            current_state = self.context.current_state.value
            state_descriptions = {
                "greeting": "We're just getting started! I need to collect your information to book an appointment.",
                "collecting_info": "I'm collecting your personal information. I need your name, date of birth, phone, and email.",
                "patient_lookup": "I'm looking you up in our system to see if you're a returning patient.",
                "new_patient_registration": "I'm registering you as a new patient in our system.",
                "doctor_selection": "I need to know which doctor you'd like to see.",
                "scheduling": "I'm helping you select an appointment time.",
                "insurance_collection": "I need your insurance information to complete the booking.",
                "confirmation": "I'm confirming your appointment details.",
                "completed": "Your appointment has been successfully booked!"
            }
            return state_descriptions.get(current_state, "I'm here to help you book an appointment!")
        
        return None  # Not a context question
    
    def _route_to_agent(self, user_input: str) -> AgentResponse:
        """Route message to the appropriate agent based on current state"""
        
        if self.context.current_state == ConversationState.GREETING:
            return self._handle_greeting(user_input)
        
        elif self.context.current_state == ConversationState.COLLECTING_INFO:
            return self._handle_info_collection(user_input)
        
        elif self.context.current_state == ConversationState.PATIENT_LOOKUP:
            return self._handle_patient_lookup(user_input)
        
        elif self.context.current_state == ConversationState.NEW_PATIENT_REGISTRATION:
            return self._handle_new_patient_registration(user_input)
        
        elif self.context.current_state == ConversationState.DOCTOR_SELECTION:
            return self._handle_doctor_selection(user_input)
        
        elif self.context.current_state == ConversationState.SCHEDULING:
            return self._handle_scheduling(user_input)
        
        elif self.context.current_state == ConversationState.INSURANCE_COLLECTION:
            return self._handle_insurance_collection(user_input)
        
        elif self.context.current_state == ConversationState.CONFIRMATION:
            return self._handle_confirmation(user_input)
        
        else:
            # Default to greeting
            return self._handle_greeting(user_input)
    
    def _handle_greeting(self, user_input: str) -> AgentResponse:
        """Handle greeting using information collector agent"""
        
        result = self.information_collector.process_greeting(user_input, self.context.conversation_history)
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(result.next_state),
            patient_info=result.patient_info,
            appointment_info=self.context.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=self.context.available_slots
        )
        
        return AgentResponse(
            success=result.success,
            message=result.message,
            next_state=ConversationState(result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.INFORMATION_COLLECTOR
        )
    
    def _handle_info_collection(self, user_input: str) -> AgentResponse:
        """Handle information collection using information collector agent"""
        
        result = self.information_collector.collect_information(
            user_input, 
            self.context.patient_info, 
            self.context.conversation_history
        )
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(result.next_state),
            patient_info=result.patient_info,
            appointment_info=self.context.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=self.context.available_slots
        )
        
        return AgentResponse(
            success=result.success,
            message=result.message,
            next_state=ConversationState(result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.INFORMATION_COLLECTOR
        )
    
    def _handle_patient_lookup(self, user_input: str) -> AgentResponse:
        """Handle patient lookup using patient management agent"""
        
        result = self.patient_manager.lookup_patient(self.context.patient_info, self.context.conversation_history)
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(result.next_state),
            patient_info=result.patient if result.patient else self.context.patient_info,
            appointment_info=self.context.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=self.context.available_slots
        )
        
        return AgentResponse(
            success=result.found,
            message=result.message,
            next_state=ConversationState(result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.PATIENT_MANAGER
        )
    
    def _handle_new_patient_registration(self, user_input: str) -> AgentResponse:
        """Handle new patient registration using patient management agent"""
        
        # Check if this is a simple confirmation response (like "ok", "yes", "sure")
        user_input_lower = user_input.lower().strip()
        simple_responses = ["ok", "okay", "yes", "yeah", "yep", "sure", "alright", "fine", "good", "great"]
        
        if user_input_lower in simple_responses:
            # Check if user is returning and show appropriate message
            is_returning = self.user_manager.is_returning_user(self.context.patient_info)
            
            if is_returning:
                welcome_message = f"👋 **Welcome back, {self.context.patient_info.first_name}!**\n\n"
                welcome_message += f"I see you're a **returning patient**. We'll book a **30-minute appointment** for you.\n\n"
                welcome_message += "Let me show you the available doctors:"
            else:
                welcome_message = f"👋 **Welcome, {self.context.patient_info.first_name}!**\n\n"
                welcome_message += f"As a **new patient**, we'll book a **60-minute appointment** for you.\n\n"
                welcome_message += "Let me show you the available doctors:"
            
            # Add welcome message to chat history
            self.context.conversation_history.append({
                'role': 'assistant',
                'content': welcome_message,
                'timestamp': datetime.now()
            })
            
            # User is confirming - directly show doctor list
            return self._handle_doctor_selection(user_input)
        
        # First collect any additional information
        collection_result = self.information_collector.collect_information(
            user_input, 
            self.context.patient_info, 
            self.context.conversation_history
        )
        
        # If all information is collected, register user and go to doctor selection
        if collection_result.success:
            # Check if user is returning before registration
            is_returning = self.user_manager.is_returning_user(collection_result.patient_info)
            
            # Register user with user manager
            registration_result = self.user_manager.register_user(collection_result.patient_info)
            
            # Update patient info with registration details
            collection_result.patient_info.patient_id = registration_result['user_id']
            collection_result.patient_info.patient_type = registration_result['patient_type']
            
            # Show appropriate message based on patient type
            if is_returning:
                welcome_message = f"👋 **Welcome back, {collection_result.patient_info.first_name}!**\n\n"
                welcome_message += f"I see you're a **returning patient**. We'll book a **30-minute appointment** for you.\n\n"
                welcome_message += "Let me show you the available doctors:"
            else:
                welcome_message = f"👋 **Welcome, {collection_result.patient_info.first_name}!**\n\n"
                welcome_message += f"As a **new patient**, we'll book a **60-minute appointment** for you.\n\n"
                welcome_message += "Let me show you the available doctors:"
            
            # Add welcome message to chat history
            self.context.conversation_history.append({
                'role': 'assistant',
                'content': welcome_message,
                'timestamp': datetime.now()
            })
            
            # Go directly to doctor selection
            return self._handle_doctor_selection(user_input)
        
        # Then attempt registration
        registration_result = self.patient_manager.register_new_patient(
            collection_result.patient_info, 
            self.context.conversation_history
        )
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(registration_result.next_state),
            patient_info=registration_result.patient,
            appointment_info=self.context.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=self.context.available_slots
        )
        
        return AgentResponse(
            success=registration_result.success,
            message=registration_result.message,
            next_state=ConversationState(registration_result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.PATIENT_MANAGER
        )
    
    def _handle_doctor_selection(self, user_input: str) -> AgentResponse:
        """Handle doctor selection using scheduling agent"""
        
        result = self.scheduler.handle_doctor_selection(
            user_input, 
            self.context.patient_info, 
            self.context.conversation_history
        )
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(result.next_state),
            patient_info=self.context.patient_info,
            appointment_info=result.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=result.available_slots
        )
        
        return AgentResponse(
            success=result.success,
            message=result.message,
            next_state=ConversationState(result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.SCHEDULER
        )
    
    def _handle_scheduling(self, user_input: str) -> AgentResponse:
        """Handle appointment scheduling using scheduling agent"""
        
        if not self.context.appointment_info:
            return AgentResponse(
                success=False,
                message="I need to know which doctor you'd like to see first.",
                next_state=ConversationState.DOCTOR_SELECTION,
                updated_context=self.context,
                agent_used=AgentType.SCHEDULER
            )
        
        result = self.scheduler.handle_appointment_scheduling(
            user_input, 
            self.context.appointment_info, 
            self.context.conversation_history
        )
        
        # Update context
        updated_context = ConversationContext(
            current_state=ConversationState(result.next_state),
            patient_info=self.context.patient_info,
            appointment_info=result.appointment_info,
            conversation_history=self.context.conversation_history,
            available_doctors=self.context.available_doctors,
            available_slots=result.available_slots
        )
        
        return AgentResponse(
            success=result.success,
            message=result.message,
            next_state=ConversationState(result.next_state),
            updated_context=updated_context,
            agent_used=AgentType.SCHEDULER
        )
    
    def _handle_insurance_collection(self, user_input: str) -> AgentResponse:
        """Handle insurance information collection"""
        
        # Extract insurance information using Gemini
        entities = self.gemini.extract_entities(user_input)
        
        # Initialize insurance info if not exists
        if not self.context.appointment_info.insurance:
            self.context.appointment_info.insurance = InsuranceInfo()
        
        # Update insurance information
        if entities.get("insurance_provider"):
            self.context.appointment_info.insurance.carrier = entities["insurance_provider"]
        
        if entities.get("insurance_id"):
            self.context.appointment_info.insurance.member_id = entities["insurance_id"]
        
        # Check if we have all required insurance information
        if (self.context.appointment_info.insurance.carrier and 
            self.context.appointment_info.insurance.member_id):
            
            # Generate confirmation response
            context = f"Insurance collected: {self.context.appointment_info.insurance.carrier}"
            response = self.gemini.generate_response(user_input, context, "insurance_handler")
            
            if not response or len(response) < 20:
                response = f"Perfect! I have your insurance information. Let me confirm your appointment details."
            
            # Update context
            updated_context = ConversationContext(
                current_state=ConversationState.CONFIRMATION,
                patient_info=self.context.patient_info,
                appointment_info=self.context.appointment_info,
                conversation_history=self.context.conversation_history,
                available_doctors=self.context.available_doctors,
                available_slots=self.context.available_slots
            )
            
            return AgentResponse(
                success=True,
                message=response,
                next_state=ConversationState.CONFIRMATION,
                updated_context=updated_context,
                agent_used=AgentType.INSURANCE_HANDLER
            )
        else:
            # Still need more insurance information
            missing_info = []
            if not self.context.appointment_info.insurance.carrier:
                missing_info.append("insurance provider")
            if not self.context.appointment_info.insurance.member_id:
                missing_info.append("insurance ID/policy number")
            
            context = f"Need insurance information: {', '.join(missing_info)}"
            response = self.gemini.generate_response(user_input, context, "insurance_handler")
            
            if not response or len(response) < 20:
                response = f"To complete your appointment booking, I need your {' and '.join(missing_info)}."
            
            return AgentResponse(
                success=False,
                message=response,
                next_state=ConversationState.INSURANCE_COLLECTION,
                updated_context=self.context,
                agent_used=AgentType.INSURANCE_HANDLER
            )
    
    def _handle_confirmation(self, user_input: str) -> AgentResponse:
        """Handle appointment confirmation"""
        
        # Generate confirmation message
        context = f"Confirming appointment for {self.context.patient_info.first_name}"
        response = self.gemini.generate_response(user_input, context, "confirmation_agent")
        
        if not response or len(response) < 20:
            response = self._generate_confirmation_message()
        
        # Save appointment
        self._save_appointment()
        
        # Reset for next conversation
        updated_context = ConversationContext(
            current_state=ConversationState.GREETING,
            patient_info=PatientInfo(),
            appointment_info=None,
            conversation_history=[],
            available_doctors=self.context.available_doctors,
            available_slots=[]
        )
        
        return AgentResponse(
            success=True,
            message=response,
            next_state=ConversationState.GREETING,
            updated_context=updated_context,
            agent_used=AgentType.CONFIRMATION_AGENT
        )
    
    def _generate_confirmation_message(self) -> str:
        """Generate appointment confirmation message"""
        
        appointment = self.context.appointment_info
        patient = self.context.patient_info
        
        return f"""
🎉 **APPOINTMENT CONFIRMED!** 🎉

👤 **Patient Information:**
• Name: {patient.first_name} {patient.last_name}
• Type: {patient.patient_type} Patient

📅 **Appointment Details:**
• Date: {appointment.date}
• Time: {appointment.time}
• Doctor: {appointment.doctor}
• Duration: {appointment.duration} minutes

💳 **Insurance Information:**
• Carrier: {appointment.insurance.carrier if appointment.insurance else 'N/A'}
• Member ID: {appointment.insurance.member_id if appointment.insurance else 'N/A'}

✅ **Next Steps:**
Your appointment has been saved to our system. You'll receive:
1. 📧 An intake form via email
2. 📱 Automated reminders before your appointment

Is there anything else I can help you with?
        """.strip()
    
    def _save_appointment(self):
        """Save appointment to database"""
        
        appointment_data = {
            "PatientName": f"{self.context.patient_info.first_name} {self.context.patient_info.last_name}".strip(),
            "DOB": self.context.patient_info.dob,
            "Phone": self.context.patient_info.phone,
            "Email": self.context.patient_info.email,
            "Doctor": self.context.appointment_info.doctor,
            "Date": self.context.appointment_info.date,
            "Time": self.context.appointment_info.time,
            "Duration": self.context.appointment_info.duration,
            "PatientType": self.context.patient_info.patient_type,
            "InsuranceCarrier": self.context.appointment_info.insurance.carrier if self.context.appointment_info.insurance else "N/A",
            "MemberID": self.context.appointment_info.insurance.member_id if self.context.appointment_info.insurance else "N/A",
            "GroupNumber": self.context.appointment_info.insurance.group_number if self.context.appointment_info.insurance else "N/A",
            "Status": "Confirmed",
            "CreatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            existing_appointments = pd.read_excel("data/appointments.xlsx")
            appointments_df = pd.concat([existing_appointments, pd.DataFrame([appointment_data])], ignore_index=True)
        except FileNotFoundError:
            appointments_df = pd.DataFrame([appointment_data])
        
        appointments_df.to_excel("data/appointments.xlsx", index=False)
    
    def reset_conversation(self):
        """Reset conversation state for new patient"""
        
        self.context = ConversationContext(
            current_state=ConversationState.GREETING,
            patient_info=PatientInfo(),
            appointment_info=None,
            conversation_history=[],
            available_doctors=list(self.schedules_db['Doctor'].unique()) if not self.schedules_db.empty else [],
            available_slots=[]
        )
    
    def get_conversation_state(self) -> ConversationState:
        """Get current conversation state"""
        return self.context.current_state
    
    def get_patient_info(self) -> PatientInfo:
        """Get current patient information"""
        return self.context.patient_info
    
    def get_appointment_info(self) -> Optional[AppointmentInfo]:
        """Get current appointment information"""
        return self.context.appointment_info
