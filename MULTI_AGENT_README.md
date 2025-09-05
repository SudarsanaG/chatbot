# Multi-Agent Medical Scheduling System

## Overview

This system has been upgraded to use a **multi-agent architecture** powered by **Google's Gemini 2.0 Flash API**. The system now consists of specialized agents that work together to provide a more intelligent and efficient medical appointment scheduling experience.

## Architecture

### 🤖 Multi-Agent System Components

1. **Information Collection Agent** (`src/information_collector_agent.py`)
   - Specializes in collecting and validating patient information
   - Handles greetings and initial patient data gathering
   - Validates email, phone, and date formats

2. **Patient Management Agent** (`src/patient_management_agent.py`)
   - Manages patient database operations
   - Handles patient lookup and registration
   - Maintains patient records and statistics

3. **Scheduling Agent** (`src/scheduling_agent.py`)
   - Handles doctor selection and appointment scheduling
   - Manages available time slots
   - Processes appointment bookings

4. **Multi-Agent Coordinator** (`src/multi_agent_coordinator.py`)
   - Orchestrates communication between agents
   - Manages conversation flow and state transitions
   - Handles insurance collection and confirmation

5. **Gemini API Client** (`src/gemini_client.py`)
   - Interfaces with Google's Gemini 2.0 Flash API
   - Handles entity extraction and response generation
   - Provides intelligent conversation management

## Key Features

### 🚀 Enhanced Capabilities

- **Intelligent Entity Extraction**: Uses Gemini AI to extract patient information from natural language
- **Contextual Responses**: Generates appropriate responses based on conversation context
- **Specialized Agents**: Each agent focuses on specific aspects of the scheduling process
- **Improved Accuracy**: Better understanding of user intent and information extraction
- **Flexible Conversation Flow**: Handles various conversation patterns and edge cases

### 🔧 Technical Improvements

- **API Integration**: Direct integration with Gemini 2.0 Flash API
- **Modular Design**: Easy to extend and modify individual agents
- **Error Handling**: Robust error handling and fallback mechanisms
- **State Management**: Sophisticated conversation state tracking
- **Data Validation**: Enhanced validation for patient information

## Configuration

### Environment Variables

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# LLM Provider Selection
LLM_PROVIDER=gemini  # or "openai" for OpenAI integration
```

### API Key Setup

The system is pre-configured with a Gemini API key. To use your own key:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable: `export GEMINI_API_KEY=your_key_here`
3. Or update the key in `config.py`

## Usage

### Running the System

```bash
# Run the Streamlit web interface
streamlit run main_chatbot.py

# Test the multi-agent system
python test_multi_agent.py
```

### API Integration

```python
from src.multi_agent_system import MultiAgentMedicalSchedulingSystem

# Create system instance
system = MultiAgentMedicalSchedulingSystem()

# Process messages
response = system.process_message("Hi, I'd like to book an appointment")
print(response)

# Get system status
status = system.get_system_status()
print(f"Current state: {status['conversation_state']}")
```

## Conversation Flow

### 1. **Greeting & Information Collection**
- User greets the system
- Information Collection Agent gathers basic patient details
- Validates and processes patient information

### 2. **Patient Management**
- Patient Management Agent looks up existing patients
- Registers new patients if not found
- Updates patient database

### 3. **Doctor Selection & Scheduling**
- Scheduling Agent presents available doctors
- Handles doctor selection with fuzzy matching
- Shows available appointment slots

### 4. **Appointment Booking**
- Processes time slot selection
- Books the appointment
- Updates schedule database

### 5. **Insurance & Confirmation**
- Collects insurance information
- Generates appointment confirmation
- Saves complete appointment record

## Agent Specialization

### Information Collection Agent
- **Purpose**: Collect and validate patient information
- **Capabilities**:
  - Natural language processing for information extraction
  - Email, phone, and date validation
  - Contextual conversation management
  - Missing information detection

### Patient Management Agent
- **Purpose**: Manage patient database operations
- **Capabilities**:
  - Patient lookup with fuzzy matching
  - New patient registration
  - Database statistics and reporting
  - Patient information updates

### Scheduling Agent
- **Purpose**: Handle appointment scheduling
- **Capabilities**:
  - Doctor selection with intelligent matching
  - Available slot management
  - Appointment booking and confirmation
  - Schedule conflict resolution

### Multi-Agent Coordinator
- **Purpose**: Orchestrate agent interactions
- **Capabilities**:
  - Conversation state management
  - Agent routing and coordination
  - Insurance information collection
  - Final appointment confirmation

## Benefits of Multi-Agent Architecture

### 🎯 **Specialization**
- Each agent focuses on specific tasks
- Better accuracy and efficiency
- Easier maintenance and updates

### 🔄 **Scalability**
- Easy to add new agents
- Modular design allows independent development
- Can handle multiple conversation threads

### 🛡️ **Reliability**
- Fault isolation between agents
- Fallback mechanisms for each component
- Better error handling and recovery

### 🧠 **Intelligence**
- Context-aware responses
- Better understanding of user intent
- Improved natural language processing

## Testing

### Run Tests

```bash
# Test the complete system
python test_multi_agent.py

# Test individual components
python -c "from src.gemini_client import GeminiClient; print('Gemini client test passed')"
```

### Test Coverage

The test suite covers:
- Full conversation flow
- Individual agent functionality
- API integration
- Error handling
- Data validation

## Migration from Single Agent

The system maintains backward compatibility while providing enhanced functionality:

- **Same Interface**: The main chatbot interface remains unchanged
- **Enhanced Responses**: More intelligent and contextual responses
- **Better Accuracy**: Improved entity extraction and understanding
- **Robust Error Handling**: Better handling of edge cases and errors

## Future Enhancements

### Planned Features
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **Multi-language Support**: Support for multiple languages
- **Advanced Analytics**: Conversation analytics and insights
- **Integration APIs**: REST API for external system integration
- **Mobile App**: Native mobile application

### Extensibility
- **Custom Agents**: Easy to add new specialized agents
- **Plugin System**: Modular plugin architecture
- **Custom Workflows**: Configurable conversation flows
- **External Integrations**: Easy integration with external systems

## Troubleshooting

### Common Issues

1. **API Key Issues**
   ```bash
   # Check if API key is set
   echo $GEMINI_API_KEY
   
   # Set API key
   export GEMINI_API_KEY=your_key_here
   ```

2. **Import Errors**
   ```bash
   # Install required dependencies
   pip install -r requirements.txt
   
   # Check Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Data Issues**
   ```bash
   # Ensure data files exist
   ls -la data/
   
   # Generate test data if needed
   python -c "from src.data_generator import MedicalDataGenerator; MedicalDataGenerator().create_data_files()"
   ```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test files for examples
3. Check the configuration in `config.py`
4. Verify API key and network connectivity

## License

This project maintains the same license as the original system.
