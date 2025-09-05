#!/usr/bin/env python3
"""
Simple test script for LLM agent
"""

import os
import sys

# Set the API key
os.environ["OPENAI_API_KEY"] = "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"

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
