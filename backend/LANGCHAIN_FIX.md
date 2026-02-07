# LangChain Import Error Fix

If you're getting `ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'`, here's how to fix it:

## Quick Fix

### Option 1: Reinstall LangChain (Recommended)

```bash
cd backend
pip uninstall langchain langchain-core langchain-openai -y
pip install "langchain>=0.1.0,<0.3.0" langchain-openai langchain-core
```

### Option 2: Check Your LangChain Version

```bash
pip show langchain
```

If you have version 0.3.0 or higher, the API has changed. Use:

```bash
pip install "langchain<0.3.0" langchain-openai langchain-core
```

### Option 3: Use Compatible Versions

```bash
pip install langchain==0.2.16 langchain-openai==0.1.23 langchain-core==0.2.38
```

## Check What's Available

Run the diagnostic script:

```bash
cd backend
python check_langchain_imports.py
```

This will show you what imports are actually available in your installation.

## Server Will Still Start

The server has been updated to handle LangChain import errors gracefully:

- ✅ Server will start even if LangChain imports fail
- ✅ Other endpoints (screen-control, fields, health) will work
- ⚠️ Form filler endpoints will return 503 with error message

## Test Server Start

```bash
cd backend
./run_server.sh
```

The server should start successfully. You'll see an error message when trying to use form-filler endpoints if LangChain isn't working, but the server itself will be running.

## Verify Installation

After reinstalling, test the imports:

```python
python -c "from langchain.agents import AgentExecutor, create_openai_tools_agent; print('✅ Imports work!')"
```

If this works, restart the server and the form-filler endpoints should work.

