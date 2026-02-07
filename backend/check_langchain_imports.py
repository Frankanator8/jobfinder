#!/usr/bin/env python3
"""Check what LangChain imports are available"""
import sys

print("Checking LangChain imports...")
print("=" * 60)

# Check AgentExecutor
print("\n1. Checking AgentExecutor:")
try:
    from langchain.agents import AgentExecutor
    print("   ✅ langchain.agents.AgentExecutor")
except ImportError as e:
    print(f"   ❌ langchain.agents.AgentExecutor: {e}")
    try:
        from langchain_core.agents import AgentExecutor
        print("   ✅ langchain_core.agents.AgentExecutor")
    except ImportError as e2:
        print(f"   ❌ langchain_core.agents.AgentExecutor: {e2}")
        try:
            from langchain.agents.agent_executor import AgentExecutor
            print("   ✅ langchain.agents.agent_executor.AgentExecutor")
        except ImportError as e3:
            print(f"   ❌ langchain.agents.agent_executor.AgentExecutor: {e3}")

# Check create_openai_tools_agent
print("\n2. Checking create_openai_tools_agent:")
try:
    from langchain.agents import create_openai_tools_agent
    print("   ✅ langchain.agents.create_openai_tools_agent")
except ImportError as e:
    print(f"   ❌ langchain.agents.create_openai_tools_agent: {e}")

# Check what's in langchain.agents
print("\n3. What's available in langchain.agents:")
try:
    import langchain.agents
    print(f"   Available: {dir(langchain.agents)}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)

