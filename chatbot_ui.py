"""
Web-based Chatbot UI using FastAPI and WebSockets
Real-time chat interface for RagaAI Medical Scheduling Agent
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import Dict, List
from src.agent import MedicalSchedulingAgent, ConversationState
import uvicorn
import os

app = FastAPI(title="RagaAI Medical Scheduling Agent")

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_instances: Dict[WebSocket, MedicalSchedulingAgent] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Create a new agent instance for this connection
        self.agent_instances[websocket] = MedicalSchedulingAgent()
        print(f"New connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.agent_instances:
            del self.agent_instances[websocket]
        print(f"Connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# HTML template for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RagaAI Medical Scheduling Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0fdf4 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
            padding: 20px;
        }
        
        .chat-container {
            width: 90%;
            max-width: 900px;
            height: 85vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(255, 255, 255, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .chat-header {
            background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%);
            color: white;
            padding: 24px;
            text-align: center;
            position: relative;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chat-header h1 {
            font-size: 28px;
            margin-bottom: 8px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .chat-header p {
            opacity: 0.9;
            font-size: 15px;
            font-weight: 400;
        }
        
        .status-indicator {
            position: absolute;
            top: 24px;
            right: 24px;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse 2s infinite;
            box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
            scroll-behavior: smooth;
        }
        
        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.2);
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            animation: fadeInUp 0.3s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.assistant {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 75%;
            padding: 16px 20px;
            border-radius: 20px;
            word-wrap: break-word;
            position: relative;
            line-height: 1.5;
            font-size: 15px;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            border-bottom-right-radius: 6px;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
        }
        
        .message.assistant .message-content {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .message.assistant.success .message-content {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border-color: #10b981;
            color: #065f46;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
        }
        
        .message.assistant.error .message-content {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border-color: #ef4444;
            color: #991b1b;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
        }
        
        .message-time {
            font-size: 12px;
            opacity: 0.6;
            margin-top: 6px;
            font-weight: 400;
        }
        
        .chat-input-container {
            padding: 24px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(229, 231, 235, 0.5);
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 28px;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }
        
        .chat-input:focus {
            border-color: #059669;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
            background: white;
        }
        
        .send-button {
            padding: 16px 24px;
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            border: none;
            border-radius: 28px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
        }
        
        .send-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(5, 150, 105, 0.4);
        }
        
        .send-button:active {
            transform: translateY(0);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: 0 2px 6px rgba(5, 150, 105, 0.2);
        }
        
        .quick-actions {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .quick-action {
            padding: 10px 16px;
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .quick-action:hover {
            background: rgba(5, 150, 105, 0.1);
            border-color: #059669;
            transform: translateY(-1px);
        }
        
        .typing-indicator {
            display: none;
            padding: 16px 20px;
            background: white;
            border-radius: 20px;
            border-bottom-left-radius: 6px;
            margin-bottom: 20px;
            max-width: 75%;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #059669;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            left: 20px;
            padding: 12px 18px;
            border-radius: 24px;
            color: white;
            font-size: 13px;
            font-weight: 600;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .connection-status.connected {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        
        .connection-status.disconnected {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
        
        .appointment-summary {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 1px solid #10b981;
            border-radius: 16px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
        }
        
        .appointment-summary h4 {
            color: #065f46;
            margin-bottom: 12px;
            font-size: 18px;
            font-weight: 700;
        }
        
                 .appointment-summary p {
             margin: 6px 0;
             font-size: 15px;
             color: #047857;
         }
         
         .doctor-selection {
             background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
             border: 1px solid #0ea5e9;
             border-radius: 16px;
             padding: 20px;
             margin: 15px 0;
             box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
         }
         
         .doctor-selection h4 {
             color: #0c4a6e;
             margin-bottom: 15px;
             font-size: 18px;
             font-weight: 700;
         }
         
         .doctor-search {
             margin-bottom: 15px;
         }
         
         .doctor-search input {
             width: 100%;
             padding: 12px 16px;
             border: 2px solid #e5e7eb;
             border-radius: 12px;
             font-size: 14px;
             outline: none;
             transition: all 0.3s ease;
             background: white;
         }
         
         .doctor-search input:focus {
             border-color: #0ea5e9;
             box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
         }
         
         .doctor-grid {
             display: grid;
             grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
             gap: 10px;
             max-height: 200px;
             overflow-y: auto;
         }
         
         .doctor-option {
             padding: 12px 16px;
             background: white;
             border: 2px solid #e5e7eb;
             border-radius: 12px;
             cursor: pointer;
             font-size: 14px;
             font-weight: 500;
             transition: all 0.3s ease;
             text-align: center;
         }
         
         .doctor-option:hover {
             border-color: #0ea5e9;
             background: #f0f9ff;
             transform: translateY(-1px);
         }
         
         .doctor-option.selected {
             border-color: #059669;
             background: #ecfdf5;
             color: #065f46;
         }
         
         .doctor-grid::-webkit-scrollbar {
             width: 6px;
         }
         
         .doctor-grid::-webkit-scrollbar-track {
             background: transparent;
         }
         
         .doctor-grid::-webkit-scrollbar-thumb {
             background: rgba(0, 0, 0, 0.1);
             border-radius: 3px;
         }
         
         .change-selection-btn {
             padding: 8px 16px;
             background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
             color: white;
             border: none;
             border-radius: 12px;
             cursor: pointer;
             font-size: 13px;
             font-weight: 600;
             transition: all 0.3s ease;
             box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
         }
         
         .change-selection-btn:hover {
             transform: translateY(-1px);
             box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
         }
     </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connecting...</div>
    
    <div class="chat-container">
        <div class="chat-header">
            <div class="status-indicator"></div>
            <h1>🏥 RagaAI Medical Scheduling Agent</h1>
            <p>Your AI assistant for medical appointment booking</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">
                    <div>Hello! I'm your AI medical scheduling assistant. I can help you book appointments, check availability, and manage your medical visits. How can I assist you today?</div>
                    <div class="message-time" id="welcomeTime"></div>
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="quick-actions">
                <button class="quick-action" onclick="sendQuickMessage('Hi, I\\'d like to book an appointment')">Book Appointment</button>
                <button class="quick-action" onclick="sendQuickMessage('What doctors are available?')">Available Doctors</button>
                <button class="quick-action" onclick="sendQuickMessage('Help')">Help</button>
                <button class="quick-action" onclick="resetConversation()">Reset</button>
            </div>
            
            <div class="chat-input-wrapper">
                <input type="text" class="chat-input" id="messageInput" placeholder="Type your message here..." autocomplete="off">
                <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let isConnected = false;
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                isConnected = true;
                updateConnectionStatus('connected', 'Connected');
                console.log('Connected to WebSocket');
            };
            
                         ws.onmessage = function(event) {
                 const data = JSON.parse(event.data);
                 hideTypingIndicator();
                 
                 if (data.type === 'message') {
                     addMessage(data.message, 'assistant', data.message_type || 'normal');
                     
                     // Check if this is a doctor selection message
                     if (data.message.includes('Which doctor would you like to see?') && data.message.includes('Available doctors:')) {
                         const doctorList = data.message.split('Available doctors: ')[1];
                         showDoctorSelection(doctorList);
                     }
                 } else if (data.type === 'appointment_summary') {
                     showAppointmentSummary(data.appointment);
                 } else if (data.type === 'status') {
                     updateConnectionStatus('connected', data.message);
                 }
             };
            
            ws.onclose = function(event) {
                isConnected = false;
                updateConnectionStatus('disconnected', 'Disconnected');
                console.log('WebSocket connection closed');
                
                // Try to reconnect after 3 seconds
                setTimeout(connect, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus('disconnected', 'Connection Error');
            };
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (message && isConnected) {
                addMessage(message, 'user');
                input.value = '';
                
                // Show typing indicator
                showTypingIndicator();
                
                // Send message to server
                ws.send(JSON.stringify({
                    type: 'message',
                    message: message
                }));
            }
        }
        
        function sendQuickMessage(message) {
            if (isConnected) {
                addMessage(message, 'user');
                showTypingIndicator();
                
                ws.send(JSON.stringify({
                    type: 'message',
                    message: message
                }));
            }
        }
        
        function resetConversation() {
            if (isConnected) {
                ws.send(JSON.stringify({
                    type: 'reset'
                }));
                
                // Clear chat messages except welcome
                const chatMessages = document.getElementById('chatMessages');
                const welcomeMessage = chatMessages.querySelector('.message.assistant');
                chatMessages.innerHTML = '';
                chatMessages.appendChild(welcomeMessage);
            }
        }
        
        function addMessage(content, sender, messageType = 'normal') {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            if (sender === 'assistant' && messageType !== 'normal') {
                messageDiv.classList.add(messageType);
            }
            
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div>${content}</div>
                    <div class="message-time">${timeString}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
                 function showAppointmentSummary(appointment) {
             const chatMessages = document.getElementById('chatMessages');
             const summaryDiv = document.createElement('div');
             summaryDiv.className = 'appointment-summary';
             
             summaryDiv.innerHTML = `
                 <h4>🎉 Appointment Confirmed!</h4>
                 <p><strong>Patient:</strong> ${appointment.patient.first_name} ${appointment.patient.last_name}</p>
                 <p><strong>Doctor:</strong> ${appointment.doctor}</p>
                 <p><strong>Date:</strong> ${appointment.date}</p>
                 <p><strong>Time:</strong> ${appointment.time}</p>
                 <p><strong>Duration:</strong> ${appointment.duration} minutes</p>
                 <p><strong>Type:</strong> ${appointment.patient.patient_type} Patient</p>
             `;
             
             chatMessages.appendChild(summaryDiv);
             chatMessages.scrollTop = chatMessages.scrollHeight;
         }
         
         function showDoctorSelection(doctors) {
             const chatMessages = document.getElementById('chatMessages');
             const selectionDiv = document.createElement('div');
             selectionDiv.className = 'doctor-selection';
             selectionDiv.id = 'doctorSelection';
             
             const doctorList = doctors.split(', ').map(doctor => doctor.trim());
             
             selectionDiv.innerHTML = `
                 <h4>👨‍⚕️ Select Your Doctor</h4>
                 <div class="doctor-search">
                     <input type="text" id="doctorSearch" placeholder="Search doctors by name..." onkeyup="filterDoctors()">
                 </div>
                 <div class="doctor-grid" id="doctorGrid">
                     ${doctorList.map(doctor => `
                         <div class="doctor-option" onclick="selectDoctor('${doctor}')" data-name="${doctor.toLowerCase()}">
                             ${doctor}
                         </div>
                     `).join('')}
                 </div>
                 <div class="selection-actions" id="selectionActions" style="display: none; margin-top: 15px; text-align: center;">
                     <button class="change-selection-btn" onclick="resetDoctorSelection()">🔄 Change Selection</button>
                 </div>
             `;
             
             chatMessages.appendChild(selectionDiv);
             chatMessages.scrollTop = chatMessages.scrollHeight;
         }
         
         function filterDoctors() {
             const searchTerm = document.getElementById('doctorSearch').value.toLowerCase();
             const doctorOptions = document.querySelectorAll('.doctor-option');
             
             doctorOptions.forEach(option => {
                 const doctorName = option.getAttribute('data-name');
                 if (doctorName.includes(searchTerm)) {
                     option.style.display = 'block';
                 } else {
                     option.style.display = 'none';
                 }
             });
         }
         
         function selectDoctor(doctorName) {
             // Mark the selected doctor as selected
             const doctorOptions = document.querySelectorAll('.doctor-option');
             doctorOptions.forEach(option => {
                 option.classList.remove('selected');
                 if (option.textContent.trim() === doctorName) {
                     option.classList.add('selected');
                 }
             });
             
             // Disable all other options to prevent multiple selections
             doctorOptions.forEach(option => {
                 if (option.textContent.trim() !== doctorName) {
                     option.style.opacity = '0.5';
                     option.style.cursor = 'not-allowed';
                     option.onclick = null;
                 }
             });
             
             // Show the change selection button
             const selectionActions = document.getElementById('selectionActions');
             if (selectionActions) {
                 selectionActions.style.display = 'block';
             }
             
             // Add a confirmation message
             const chatMessages = document.getElementById('chatMessages');
             const confirmationDiv = document.createElement('div');
             confirmationDiv.className = 'message user';
             confirmationDiv.innerHTML = `
                 <div class="message-content">
                     <div>✅ Selected: ${doctorName}</div>
                     <div class="message-time">${new Date().toLocaleTimeString()}</div>
                 </div>
             `;
             chatMessages.appendChild(confirmationDiv);
             chatMessages.scrollTop = chatMessages.scrollHeight;
             
             // Send doctor selection to server
             if (isConnected) {
                 showTypingIndicator();
                 
                 ws.send(JSON.stringify({
                     type: 'message',
                     message: doctorName
                 }));
             }
         }
         
         function resetDoctorSelection() {
             // Reset all doctor options
             const doctorOptions = document.querySelectorAll('.doctor-option');
             doctorOptions.forEach(option => {
                 option.classList.remove('selected');
                 option.style.opacity = '1';
                 option.style.cursor = 'pointer';
                 option.onclick = () => selectDoctor(option.textContent.trim());
             });
             
             // Hide the change selection button
             const selectionActions = document.getElementById('selectionActions');
             if (selectionActions) {
                 selectionActions.style.display = 'none';
             }
             
             // Clear the search input
             const searchInput = document.getElementById('doctorSearch');
             if (searchInput) {
                 searchInput.value = '';
                 filterDoctors(); // Reset the filter
             }
             
             // Add a reset message
             const chatMessages = document.getElementById('chatMessages');
             const resetDiv = document.createElement('div');
             resetDiv.className = 'message user';
             resetDiv.innerHTML = `
                 <div class="message-content">
                     <div>🔄 Selection reset - please choose a doctor</div>
                     <div class="message-time">${new Date().toLocaleTimeString()}</div>
                 </div>
             `;
             chatMessages.appendChild(resetDiv);
             chatMessages.scrollTop = chatMessages.scrollHeight;
         }
        
        function showTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'block';
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'none';
        }
        
        function updateConnectionStatus(status, message) {
            const statusElement = document.getElementById('connectionStatus');
            statusElement.className = `connection-status ${status}`;
            statusElement.textContent = message;
        }
        
        // Event listeners
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Set welcome message time
        document.getElementById('welcomeTime').textContent = new Date().toLocaleTimeString();
        
        // Connect when page loads
        connect();
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML_TEMPLATE)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "reset":
                # Reset the agent for this connection
                manager.agent_instances[websocket] = MedicalSchedulingAgent()
                await manager.send_personal_message(
                    json.dumps({
                        "type": "message",
                        "message": "🔄 Conversation reset! Hello! I'm your AI medical scheduling assistant. How can I help you today?",
                        "message_type": "normal"
                    }), 
                    websocket
                )
                continue
            
            # Get the agent instance for this connection
            agent = manager.agent_instances.get(websocket)
            if not agent:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "message",
                        "message": "❌ Agent not found. Please refresh the page.",
                        "message_type": "error"
                    }), 
                    websocket
                )
                continue
            
            # Process the message
            user_message = message_data.get("message", "")
            if user_message:
                try:
                    # Process through AI agent
                    response = agent.process_message(user_message)
                    
                    # Determine message type
                    message_type = "normal"
                    if agent.conversation_state == ConversationState.COMPLETED:
                        message_type = "success"
                    elif "error" in response.lower() or "sorry" in response.lower():
                        message_type = "error"
                    
                    # Send response
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "message",
                            "message": response,
                            "message_type": message_type
                        }), 
                        websocket
                    )
                    
                    # If appointment is completed, send summary
                    if agent.conversation_state == ConversationState.COMPLETED and agent.current_appointment:
                        appointment_data = {
                            "patient": {
                                "first_name": agent.current_appointment.patient.first_name,
                                "last_name": agent.current_appointment.patient.last_name,
                                "patient_type": agent.current_appointment.patient.patient_type
                            },
                            "doctor": agent.current_appointment.doctor,
                            "date": agent.current_appointment.date,
                            "time": agent.current_appointment.time,
                            "duration": agent.current_appointment.duration
                        }
                        
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "appointment_summary",
                                "appointment": appointment_data
                            }), 
                            websocket
                        )
                        
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "message",
                            "message": f"❌ I apologize, but I encountered an error: {str(e)}. Please try again.",
                            "message_type": "error"
                        }), 
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(manager.active_connections)}

if __name__ == "__main__":
    print("🚀 Starting RagaAI Medical Scheduling Agent Web UI...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    print("💡 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "chatbot_ui:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

