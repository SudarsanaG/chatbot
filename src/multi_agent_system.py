"""
Multi-Agent Medical Scheduling System
Main entry point for the multi-agent scheduling system using Gemini API
"""

from typing import Dict, List, Optional, Any
from src.multi_agent_coordinator import MultiAgentCoordinator
from src.agent import ConversationState, PatientInfo, AppointmentInfo
from config import Config

class MultiAgentMedicalSchedulingSystem:
    """
    Main medical scheduling system using multiple specialized agents
    """
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize the multi-agent system"""
        
        # Get API key from config or parameter
        api_key = gemini_api_key or Config.GEMINI_API_KEY
        
        # Initialize the coordinator
        self.coordinator = MultiAgentCoordinator(api_key)
        
        # System state
        self.is_active = True
        self.session_id = None
    
    def process_message(self, user_input: str, session_id: str = None) -> str:
        """
        Process user message through the multi-agent system
        
        Args:
            user_input: User's message
            session_id: Optional session identifier
            
        Returns:
            System response
        """
        
        if not self.is_active:
            return "The scheduling system is currently unavailable. Please try again later."
        
        try:
            # Process through coordinator
            response = self.coordinator.process_message(user_input)
            
            # Log the interaction (optional)
            if session_id:
                self._log_interaction(session_id, user_input, response)
            
            return response
            
        except Exception as e:
            error_message = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            return error_message
    
    def get_conversation_state(self) -> str:
        """Get current conversation state"""
        return self.coordinator.get_conversation_state().value
    
    def get_patient_info(self) -> Dict[str, Any]:
        """Get current patient information"""
        patient = self.coordinator.get_patient_info()
        return {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": patient.dob,
            "phone": patient.phone,
            "email": patient.email,
            "patient_type": patient.patient_type,
            "patient_id": patient.patient_id
        }
    
    def get_appointment_info(self) -> Optional[Dict[str, Any]]:
        """Get current appointment information"""
        appointment = self.coordinator.get_appointment_info()
        if not appointment:
            return None
        
        return {
            "doctor": appointment.doctor,
            "date": appointment.date,
            "time": appointment.time,
            "duration": appointment.duration,
            "status": appointment.status,
            "insurance": {
                "carrier": appointment.insurance.carrier if appointment.insurance else None,
                "member_id": appointment.insurance.member_id if appointment.insurance else None,
                "group_number": appointment.insurance.group_number if appointment.insurance else None
            } if appointment.insurance else None
        }
    
    def reset_conversation(self):
        """Reset conversation for new patient"""
        self.coordinator.reset_conversation()
    
    def start_new_session(self, session_id: str = None):
        """Start a new conversation session"""
        self.session_id = session_id
        self.reset_conversation()
        return "Hello! I'm your AI medical scheduling assistant. How can I help you today?"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return {
            "is_active": self.is_active,
            "session_id": self.session_id,
            "conversation_state": self.get_conversation_state(),
            "patient_info": self.get_patient_info(),
            "appointment_info": self.get_appointment_info(),
            "llm_provider": Config.LLM_PROVIDER
        }
    
    def _log_interaction(self, session_id: str, user_input: str, response: str):
        """Log interaction for debugging/monitoring"""
        # This could be enhanced to log to a database or file
        if Config.DEBUG:
            print(f"Session {session_id}: User: {user_input} | Assistant: {response}")
    
    def shutdown(self):
        """Shutdown the system"""
        self.is_active = False
        return "System shutdown complete."

# Convenience function for easy integration
def create_scheduling_system(gemini_api_key: str = None) -> MultiAgentMedicalSchedulingSystem:
    """Create a new multi-agent scheduling system"""
    return MultiAgentMedicalSchedulingSystem(gemini_api_key)

# Example usage
if __name__ == "__main__":
    # Create system
    system = create_scheduling_system()
    
    # Start conversation
    print(system.start_new_session("test_session"))
    
    # Example conversation
    test_messages = [
        "Hi, I'd like to book an appointment",
        "My name is John Smith",
        "My date of birth is 01/15/1985",
        "My phone is 555-123-4567",
        "My email is john.smith@email.com",
        "I'd like to see Dr. Johnson",
        "I'll take slot 1",
        "My insurance is Blue Cross, member ID 123456789"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = system.process_message(message)
        print(f"Assistant: {response}")
        
        # Show current state
        status = system.get_system_status()
        print(f"State: {status['conversation_state']}")
