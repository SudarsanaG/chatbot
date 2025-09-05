"""
Gemini API Client for Medical Scheduling Agent
Handles all LLM calls using Google's Gemini 2.0 Flash model
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

@dataclass
class GeminiResponse:
    """Response from Gemini API"""
    content: str
    finish_reason: str
    usage_metadata: Dict[str, Any]
    model_version: str
    response_id: str

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini client"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyDbLORVnIVp4Naa1mh2ajitROYvFUbnb_w")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
    
    def generate_content(self, prompt: str, system_prompt: str = None) -> GeminiResponse:
        """Generate content using Gemini API"""
        
        # Prepare the request payload
        parts = [{"text": prompt}]
        if system_prompt:
            parts.insert(0, {"text": f"System: {system_prompt}\n\nUser: {prompt}"})
        
        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response content
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                content = candidate["content"]["parts"][0]["text"]
                finish_reason = candidate.get("finishReason", "UNKNOWN")
            else:
                content = "I apologize, but I couldn't generate a response at this time."
                finish_reason = "ERROR"
            
            return GeminiResponse(
                content=content,
                finish_reason=finish_reason,
                usage_metadata=result.get("usageMetadata", {}),
                model_version=result.get("modelVersion", "gemini-2.0-flash"),
                response_id=result.get("responseId", "")
            )
            
        except requests.exceptions.RequestException as e:
            return GeminiResponse(
                content=f"I apologize, but I'm experiencing technical difficulties: {str(e)}",
                finish_reason="ERROR",
                usage_metadata={},
                model_version="gemini-2.0-flash",
                response_id=""
            )
        except Exception as e:
            return GeminiResponse(
                content=f"I encountered an unexpected error: {str(e)}",
                finish_reason="ERROR",
                usage_metadata={},
                model_version="gemini-2.0-flash",
                response_id=""
            )
    
    def extract_entities(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Extract entities from user input using Gemini"""
        
        system_prompt = """
        You are an expert at extracting medical appointment information from natural language.
        Extract the following information from the user's input and return it as JSON:
        
        - first_name: Patient's first name
        - last_name: Patient's last name  
        - date_of_birth: Date of birth (accepts formats like: MM/DD/YYYY, July 9 1999, 9th July 1999, etc.)
        - phone: Phone number (can be just digits like 6000545528)
        - email: Email address (like nthakuri@cisco.com)
        - insurance_provider: Insurance company name
        - insurance_id: Insurance ID/policy number
        - doctor_preference: Preferred doctor name
        - appointment_date: Desired appointment date
        - appointment_time: Desired appointment time
        - patient_type: "New" or "Returning"
        - cancellation_reason: Reason for cancellation (if applicable)
        
        IMPORTANT: 
        - If user provides just a phone number like "6000545528", extract it as phone
        - If user provides just an email like "nthakuri@cisco.com", extract it as email
        - If user provides both separated by comma like "6000545528, nthakuri@cisco.com", extract both
        - Be very flexible with phone number formats (digits only, with spaces, etc.)
        - Only extract information that is explicitly mentioned. Return null for missing fields.
        - Return only valid JSON, no additional text.
        """
        
        prompt = f"User input: {user_input}"
        if context:
            prompt = f"Context: {context}\n\nUser input: {user_input}"
        
        response = self.generate_content(prompt, system_prompt)
        
        try:
            # Try to parse JSON from the response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try simple pattern matching as fallback
            return self._fallback_entity_extraction(user_input)
    
    def _fallback_entity_extraction(self, user_input: str) -> Dict[str, Any]:
        """Fallback entity extraction using simple patterns"""
        import re
        
        entities = {}
        
        # Extract phone number (digits only or with common separators)
        phone_pattern = r'(\d{10,15})'
        phone_match = re.search(phone_pattern, user_input)
        if phone_match:
            entities["phone"] = phone_match.group(1)
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, user_input)
        if email_match:
            entities["email"] = email_match.group(0)
        
        return entities
    
    def generate_response(self, user_input: str, context: str, agent_type: str) -> str:
        """Generate contextual response based on agent type"""
        
        system_prompts = {
            "information_collector": """
            You are a friendly medical scheduling assistant specializing in collecting patient information.
            Your role is to:
            - Greet patients warmly and professionally
            - Collect necessary patient information (name, DOB, contact info)
            - Guide patients through the information collection process
            - Be patient and helpful with incomplete information
            - Keep responses concise and clear
            
            Always maintain a professional yet warm tone.
            """,
            
            "scheduler": """
            You are a medical appointment scheduling specialist.
            Your role is to:
            - Help patients select appropriate doctors
            - Show available appointment slots clearly
            - Handle scheduling conflicts and alternatives
            - Confirm appointment details
            - Provide clear scheduling information
            
            Be efficient and clear in your scheduling communications.
            """,
            
            "patient_manager": """
            You are a patient management specialist.
            Your role is to:
            - Handle patient registration and verification
            - Manage patient database lookups
            - Process new patient registrations
            - Verify existing patient information
            - Handle patient type classification (new vs returning)
            
            Be thorough and accurate in patient management tasks.
            """,
            
            "insurance_handler": """
            You are an insurance information specialist.
            Your role is to:
            - Collect insurance information professionally
            - Handle various insurance scenarios (no insurance, self-pay, etc.)
            - Verify insurance details
            - Guide patients through insurance collection
            - Be understanding of different insurance situations
            
            Be professional and helpful with insurance matters.
            """,
            
            "confirmation_agent": """
            You are a confirmation and completion specialist.
            Your role is to:
            - Provide clear appointment confirmations
            - Summarize all appointment details
            - Explain next steps to patients
            - Handle final confirmations and changes
            - Ensure patients understand their appointment details
            
            Be thorough and reassuring in confirmations.
            """
        }
        
        system_prompt = system_prompts.get(agent_type, system_prompts["information_collector"])
        
        prompt = f"Context: {context}\n\nUser: {user_input}\n\nRespond appropriately as a {agent_type.replace('_', ' ')}:"
        
        response = self.generate_content(prompt, system_prompt)
        return response.content
    
    def analyze_conversation_state(self, user_input: str, current_state: str, conversation_history: List[Dict]) -> str:
        """Analyze conversation to determine next state"""
        
        system_prompt = """
        You are a conversation state analyzer for a medical scheduling system.
        Based on the user input, current state, and conversation history, determine the most appropriate next state.
        
        Available states:
        - greeting: Initial greeting and introduction
        - collecting_info: Collecting basic patient information
        - patient_lookup: Looking up existing patient
        - new_patient_registration: Registering new patient
        - doctor_selection: Selecting a doctor
        - scheduling: Scheduling appointment time
        - insurance_collection: Collecting insurance information
        - confirmation: Confirming appointment details
        - completed: Appointment booking completed
        
        Return only the state name, nothing else.
        """
        
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
        
        prompt = f"""
        Current state: {current_state}
        User input: {user_input}
        Recent conversation history:
        {history_text}
        
        What should be the next state?
        """
        
        response = self.generate_content(prompt, system_prompt)
        return response.content.strip().lower()
