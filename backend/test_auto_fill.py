#!/usr/bin/env python3
"""
Test script for auto-fill endpoint

Usage:
    python test_auto_fill.py

This will:
1. Analyze localhost:6767 for form fields
2. Feed the results to the MCP agent
3. The agent will use screen control tools to fill the form
"""
import os
import requests
import json

# Get port from environment or default to 8000
PORT = int(os.getenv("PORT", "8000"))
BASE_URL = f"http://localhost:{PORT}/auto-fill"

def test_analyze_and_fill():
    """Test the analyze-and-fill endpoint"""
    print("=" * 60)
    print("Testing Auto-Fill Endpoint")
    print("=" * 60)
    
    # Example data to fill
    # Adjust these keys to match your form field names
    data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-1234",
        "resume": "/path/to/resume.pdf",  # For file uploads
    }
    
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure localhost:6767 is open in your browser.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print(f"\n🌐 Analyzing and filling form on localhost:6767...")
    print(f"📝 Data to fill: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-and-fill",
            json={
                "url": "http://localhost:6767",
                "data": data,
                "headless": False,  # Set to True if you want headless browser
                "screenshot_before": True,
                "screenshot_after": True,
                "delay_between_fields": 0.5
            },
            timeout=300  # 5 minute timeout for analysis + filling
        )
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Result:")
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            print("\n✅ Form filled successfully!")
            if result.get("fill_result"):
                print(f"  Filled fields: {result['fill_result'].get('filled_fields', [])}")
                if result['fill_result'].get('failed_fields'):
                    print(f"  Failed fields: {result['fill_result']['failed_fields']}")
        else:
            print(f"\n⚠️  {result.get('message', 'Unknown error')}")
        
        # Show analysis results
        if result.get("analysis"):
            print(f"\n📊 Analysis Results:")
            print(f"  Fields detected: {result['analysis'].get('field_count', 0)}")
            if result['analysis'].get('fields'):
                print(f"  Field types: {[f.get('field_type') for f in result['analysis']['fields']]}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  ./run_server.sh")
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out!")
        print("The analysis or filling took too long.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_two_step():
    """Test the two-step process: analyze first, then fill"""
    print("\n" + "=" * 60)
    print("Testing Two-Step Process")
    print("=" * 60)
    
    print("\nStep 1: Analyzing form fields...")
    try:
        # Step 1: Analyze
        analyze_response = requests.post(
            f"http://localhost:{PORT}/fields/analyze",
            json={
                "url": "http://localhost:6767",
                "headless": False
            }
        )
        analyze_response.raise_for_status()
        analysis_result = analyze_response.json()
        
        print(f"✅ Found {analysis_result.get('field_count', 0)} fields")
        print("\nDetected fields:")
        for field in analysis_result.get("fields", [])[:5]:  # Show first 5
            print(f"  - {field.get('label', 'N/A')} ({field.get('field_type')})")
        
        # Step 2: Fill
        print("\nStep 2: Filling form...")
        print("⚠️  WARNING: This will control your mouse and keyboard!")
        print("Press Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
        
        data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
        }
        
        fill_response = requests.post(
            f"{BASE_URL}/from-analysis",
            json={
                "analysis_result": analysis_result,
                "data": data,
                "screenshot_before": True,
                "screenshot_after": True,
                "delay": 0.5
            }
        )
        fill_response.raise_for_status()
        fill_result = fill_response.json()
        
        print("\n✅ Fill Result:")
        print(json.dumps(fill_result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("The agent requires an OpenAI API key to work.")
        print("Set it in your .env file or environment.")
        print()
    
    print("Choose test:")
    print("1. Analyze and fill in one step (recommended)")
    print("2. Two-step: analyze first, then fill")
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_analyze_and_fill()
    elif choice == "2":
        test_two_step()
    else:
        print("Invalid choice")

