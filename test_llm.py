#!/usr/bin/env python3
"""
Simple test script for LLM agent
"""

import os
import sys

# Check if API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY environment variable not set")
    print("Please set your OpenAI API key:")
    print("export OPENAI_API_KEY='your-api-key-here'")
    sys.exit(1)

try:
    print("🤖 Testing LLM Agent...")
    
    # Test basic imports
    from langchain_openai import ChatOpenAI
    print("✅ LangChain OpenAI imported successfully")
    
    from langgraph.graph import StateGraph
    print("✅ LangGraph imported successfully")
    
    # Test LLM initialization
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    print("✅ LLM initialized successfully")
    
    # Test basic conversation
    response = llm.invoke("Hello, how are you?")
    print(f"✅ LLM response: {response.content[:50]}...")
    
    print("\n🎉 LLM Agent is working perfectly!")
    print("You can now run: python chatbot_ui.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Please check your OpenAI API key and dependencies")
