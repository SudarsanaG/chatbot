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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #2c5aa0 0%, #1e3d72 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.assistant {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            position: relative;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .message.assistant.success .message-content {
            background: #e8f5e8;
            border-color: #4CAF50;
            color: #2e7d32;
        }
        
        .message.assistant.error .message-content {
            background: #ffebee;
            border-color: #f44336;
            color: #c62828;
        }
        
        .message-time {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 4px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .quick-action {
            padding: 8px 12px;
            background: #f0f0f0;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.3s;
        }
        
        .quick-action:hover {
            background: #e0e0e0;
        }
        
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            margin-bottom: 15px;
            max-width: 70%;
            border: 1px solid #e0e0e0;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
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
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            z-index: 1000;
        }
        
        .connection-status.connected {
            background: #4CAF50;
        }
        
        .connection-status.disconnected {
            background: #f44336;
        }
        
        .appointment-summary {
            background: #e3f2fd;
            border: 1px solid #2196F3;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .appointment-summary h4 {
            color: #1976D2;
            margin-bottom: 10px;
        }
        
        .appointment-summary p {
            margin: 5px 0;
            font-size: 14px;
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

