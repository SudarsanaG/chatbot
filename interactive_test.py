"""
Interactive Test Script for RagaAI Medical Scheduling Agent
Run this to test the agent with your own inputs
"""

from src.agent import MedicalSchedulingAgent, ConversationState
import sys

def main():
    """Interactive testing of the AI agent"""
    print("🏥 RagaAI Medical Scheduling Agent - Interactive Test")
    print("=" * 60)
    print("Type 'quit' to exit, 'reset' to start over, 'help' for examples")
    print("=" * 60)
    
    # Initialize agent
    agent = MedicalSchedulingAgent()
    
    print(f"\nCurrent state: {agent.conversation_state.value}")
    print("AI: Hello! I'm your AI medical scheduling assistant. How can I help you today?")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Handle special commands
            if user_input.lower() == 'quit':
                print("Goodbye! 👋")
                break
            elif user_input.lower() == 'reset':
                agent.reset_conversation()
                print("🔄 Conversation reset!")
                print("AI: Hello! I'm your AI medical scheduling assistant. How can I help you today?")
                continue
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'status':
                print_status(agent)
                continue
            
            if not user_input:
                continue
            
            # Process through agent
            response = agent.process_message(user_input)
            
            # Display response
            print(f"AI: {response}")
            print(f"State: {agent.conversation_state.value}")
            
            # Check if conversation is complete
            if agent.conversation_state == ConversationState.COMPLETED:
                print("\n🎉 Appointment booking completed!")
                print_appointment_summary(agent)
                
                # Ask if user wants to start over
                restart = input("\nWould you like to book another appointment? (y/n): ").strip().lower()
                if restart == 'y':
                    agent.reset_conversation()
                    print("🔄 Starting new conversation...")
                    print("AI: Hello! I'm your AI medical scheduling assistant. How can I help you today?")
                else:
                    print("Thank you for using RagaAI Medical Scheduling! 👋")
                    break
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("Type 'reset' to start over or 'quit' to exit")

def print_help():
    """Print help information"""
    print("\n📋 Help - Example Conversation Flow:")
    print("-" * 40)
    print("1. 'Hi, I'd like to book an appointment'")
    print("2. 'My name is John'")
    print("3. 'My DOB is 01/15/1990'")
    print("4. 'I'd like to see Dr. Sarah Johnson'")
    print("5. 'I'll take slot 1'")
    print("6. 'My insurance is Blue Cross Blue Shield'")
    print("7. 'My member ID is BC123456789'")
    print("8. 'My group number is GRP001'")
    print("\nCommands:")
    print("- 'quit': Exit the program")
    print("- 'reset': Start a new conversation")
    print("- 'status': Show current conversation state")
    print("- 'help': Show this help message")

def print_status(agent):
    """Print current conversation status"""
    print(f"\n📊 Current Status:")
    print(f"State: {agent.conversation_state.value}")
    
    if agent.current_patient.first_name:
        print(f"Patient: {agent.current_patient.first_name}")
        print(f"Patient Type: {agent.current_patient.patient_type}")
    
    if agent.current_appointment:
        print(f"Doctor: {agent.current_appointment.doctor}")
        print(f"Date: {agent.current_appointment.date}")
        print(f"Time: {agent.current_appointment.time}")

def print_appointment_summary(agent):
    """Print appointment summary"""
    if agent.current_appointment:
        appointment = agent.current_appointment
        patient = appointment.patient
        
        print(f"\n📋 Appointment Summary:")
        print(f"Patient: {patient.first_name} {patient.last_name}")
        print(f"Type: {patient.patient_type}")
        print(f"Doctor: {appointment.doctor}")
        print(f"Date: {appointment.date}")
        print(f"Time: {appointment.time}")
        print(f"Duration: {appointment.duration} minutes")
        
        if appointment.insurance:
            print(f"Insurance: {appointment.insurance.carrier}")
            print(f"Member ID: {appointment.insurance.member_id}")
            print(f"Group: {appointment.insurance.group_number}")

if __name__ == "__main__":
    main()

