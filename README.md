# RagaAI Medical Scheduling Agent

A comprehensive AI-powered medical appointment scheduling system built with ADK (Agent Development Toolkit) principles and natural language processing capabilities.

## 🏥 Features

### Core Features (MVP-1)
- **Patient Greeting & Data Collection**: Natural conversation flow to collect patient information
- **Patient Lookup**: Intelligent search through EMR with fuzzy matching
- **Smart Scheduling**: 60-minute slots for new patients, 30-minute for returning patients
- **Calendar Integration**: Real-time availability checking and slot management
- **Insurance Collection**: Comprehensive insurance information capture
- **Appointment Confirmation**: Automated confirmation with Excel export
- **Form Distribution**: Email intake forms after appointment confirmation
- **Reminder System**: 3-tier automated reminder system with email and SMS

### Technical Features
- **ADK Framework**: Agent Development Toolkit implementation
- **NLP Processing**: Natural language understanding and entity extraction
- **Data Validation**: Comprehensive input validation and error handling
- **Excel Export**: Admin reports and data export functionality
- **Synthetic Data**: 50+ sample patients and comprehensive schedules
- **Real-time Chat**: Streamlit-based conversational interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ragaai-scheduling-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize data**
   ```bash
   python src/data_generator.py
   ```

5. **Run the application**
   ```bash
   streamlit run main_chatbot.py
   ```

## 📁 Project Structure

```
ragaai-scheduling-agent/
├── main_chatbot.py          # Main Streamlit chatbot interface
├── main.py                  # Original simple web app
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data/                   # Data storage
│   ├── patients.csv        # Patient database
│   ├── schedules.xlsx      # Doctor schedules
│   └── appointments.xlsx   # Appointment records
├── src/                    # Source code
│   ├── agent.py           # Main AI agent class
│   ├── data_generator.py  # Synthetic data generation
│   ├── reminder_system.py # Email/SMS reminder system
│   ├── excel_export.py    # Excel export functionality
│   └── utils.py           # Utility functions
├── forms/                  # Intake forms
│   └── New Patient Intake Form.pdf
├── exports/                # Generated reports
└── backups/                # Data backups
```

## 💬 Usage

### Starting a Conversation

1. **Launch the application**: Run `streamlit run main_chatbot.py`
2. **Open your browser**: Navigate to `http://localhost:8501`
3. **Start chatting**: Type your message in the chat input

### Example Conversation Flow

```
User: Hi, I'd like to book an appointment
AI: Hello! I'm your AI medical scheduling assistant. What's your first name?

User: My name is John
AI: Nice to meet you, John! What's your date of birth? (Please use MM/DD/YYYY format)

User: My DOB is 01/15/1990
AI: Welcome back, John! I found you in our system as a returning patient. 
    Which doctor would you like to see? Available doctors: Dr. Sarah Johnson, Dr. Michael Chen...

User: I'd like to see Dr. Sarah Johnson
AI: Here are the available slots:
    1. 2024-01-15 at 09:00
    2. 2024-01-15 at 14:30
    Since you're a returning patient, your appointment will be 30 minutes long. 
    Which slot would you prefer?

User: I'll take slot 2
AI: Great! I've selected 2024-01-15 at 14:30 for your 30-minute appointment with Dr. Sarah Johnson. 
    Now I need your insurance information. What's your insurance carrier?

User: Blue Cross Blue Shield
AI: Thank you. I have Blue Cross Blue Shield as your carrier. What's your member ID?

User: BC123456789
AI: Got it. What's your group number? (If you don't have one, just say 'none')

User: GRP001
AI: 🎉 APPOINTMENT CONFIRMED! 🎉
    [Detailed confirmation with all information]
```

## 🔧 Configuration

### Email Setup (Optional)
To enable real email functionality:

1. Create a `.env` file in the project root
2. Add your email credentials:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@example.com
   EMAIL_PASSWORD=your-app-password
   ```

### SMS Setup (Optional)
To enable SMS reminders:

1. Sign up for Twilio
2. Add SMS credentials to `.env`:
   ```
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_FROM_NUMBER=+1234567890
   ```

## 📊 Admin Features

### Report Generation
- **Appointments Report**: Comprehensive appointment analytics
- **Patient Database Export**: Complete patient information
- **Revenue Report**: Financial analysis and billing data
- **Daily Schedule**: Day-specific schedule export

### Data Management
- **Synthetic Data**: 50+ sample patients with realistic data
- **Schedule Management**: 30-day doctor availability
- **Backup System**: Automated data backup functionality
- **Data Validation**: Input validation and error handling

## 🧪 Testing

### Test the System
1. **Start the application**: `streamlit run main_chatbot.py`
2. **Try different scenarios**:
   - New patient registration
   - Returning patient lookup
   - Doctor selection
   - Appointment scheduling
   - Insurance collection

### Sample Test Data
The system includes 50 synthetic patients with:
- Realistic names and demographics
- Various patient types (New/Returning)
- Complete contact information
- Insurance details

## 📈 Business Logic

### Patient Classification
- **New Patients**: 60-minute appointments, full intake process
- **Returning Patients**: 30-minute appointments, streamlined process

### Scheduling Rules
- Business hours: 9 AM - 5 PM, Monday-Friday
- 30-minute time slots
- Automatic slot management
- Conflict prevention

### Reminder System
1. **First Reminder**: 3 days before appointment
2. **Second Reminder**: 1 day before (intake form check)
3. **Third Reminder**: 2 hours before (confirmation request)

## 🔍 Technical Architecture

### ADK Implementation
- **Conversation State Management**: Enum-based state tracking
- **Entity Extraction**: NLP-powered information extraction
- **Business Logic**: Rule-based appointment processing
- **Error Handling**: Comprehensive exception management

### Data Flow
1. **User Input** → NLP Processing → Entity Extraction
2. **State Routing** → Business Logic → Database Operations
3. **Response Generation** → User Interface → Confirmation

### Integration Points
- **CSV Database**: Patient information storage
- **Excel Schedules**: Doctor availability management
- **Email System**: Intake form distribution
- **SMS System**: Automated reminders
- **Excel Export**: Admin reporting

## 🚨 Error Handling

The system includes comprehensive error handling for:
- Invalid input formats
- Database connection issues
- Email/SMS delivery failures
- File system errors
- Network connectivity problems

## 📝 Development Notes

### Framework Choice: ADK
Selected ADK over LangGraph/LangChain for:
- **Simplified Development**: Built-in medical templates
- **Streamlined Process**: Pre-configured agent framework
- **Rapid Prototyping**: Faster development cycle
- **Business Focus**: Healthcare-specific optimizations

### Key Technical Decisions
1. **State Management**: Enum-based conversation states
2. **Data Storage**: CSV/Excel for simplicity and compatibility
3. **NLP Processing**: Rule-based entity extraction
4. **UI Framework**: Streamlit for rapid development
5. **Error Handling**: Graceful degradation and user feedback

## 🎯 Success Metrics

- ✅ **Functional Demo**: Complete patient booking workflow
- ✅ **Data Accuracy**: Correct patient classification and scheduling
- ✅ **Integration Success**: Excel exports and calendar management
- ✅ **Code Quality**: Clean, documented, executable codebase

## 📞 Support

For technical support or questions:
- Check the admin panel in the Streamlit interface
- Review the console output for error messages
- Ensure all dependencies are properly installed
- Verify data files are in the correct locations

## 🔄 Future Enhancements

Potential improvements for production deployment:
- Database integration (PostgreSQL/MySQL)
- Real-time calendar sync (Google Calendar, Outlook)
- Advanced NLP with OpenAI integration
- Mobile app interface
- Multi-language support
- Advanced analytics dashboard

---

**Built with ❤️ for RagaAI Medical Scheduling Challenge**

