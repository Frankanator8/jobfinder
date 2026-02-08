#!/usr/bin/env python3
"""
Comprehensive test for MCP ReAct Agent with div selection analysis

This test demonstrates the full pipeline:
1. Analyze a URL for form fields using div selection
2. Extract bounding boxes from the analysis
3. Use the MCP ReAct agent to fill the form using screen control tools
4. Verify the results

Usage:
    python test_mcp_react_agent.py

Requirements:
1. FastAPI server running: uvicorn app.main:app --reload
2. OPENAI_API_KEY set in environment
3. A form visible on screen
3. URL with a form to test (default: localhost:6767)
"""
import os
import sys
import requests
import json
from typing import Dict, Any, List

# Get port from environment or default to 8000
PORT = int(os.getenv("PORT", "8000"))
BASE_URL = f"http://localhost:{PORT}"


def analyze_form_fields(url: str, headless: bool = False) -> Dict[str, Any]:
    """
    Step 1: Analyze URL for form fields using div selection
    
    Args:
        url: URL to analyze
        headless: Whether to run browser in headless mode
        
    Returns:
        Analysis result with fields and bounding boxes
    """
    print("\n" + "=" * 70)
    print("STEP 1: Analyzing form fields using div selection")
    print("=" * 70)
    print(f"🌐 Analyzing URL: {url}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/fields/analyze",
            json={
                "url": url,
                "headless": headless
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Analysis complete!")
        print(f"   Fields detected: {result.get('field_count', 0)}")
        
        if result.get('fields'):
            print("\n📋 Detected fields:")
            for i, field in enumerate(result['fields'][:10], 1):  # Show first 10
                bbox = field.get('bounding_box', {})
                print(f"   {i}. {field.get('label', 'N/A')} ({field.get('field_type', 'unknown')})")
                print(f"      Bounding box: x={bbox.get('x')}, y={bbox.get('y')}, "
                      f"width={bbox.get('width')}, height={bbox.get('height')}")
                print(f"      Center: ({bbox.get('x', 0) + bbox.get('width', 0) // 2}, "
                      f"{bbox.get('y', 0) + bbox.get('height', 0) // 2})")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error analyzing form: {e}")
        sys.exit(1)


def test_mcp_react_agent_with_analysis(url: str, data: Dict[str, Any], headless: bool = False):
    """
    Test the full pipeline: analyze -> fill using MCP ReAct agent
    
    Args:
        url: URL to analyze and fill
        data: Data to fill into form fields
        headless: Whether to run browser in headless mode
    """
    print("\n" + "=" * 70)
    print("MCP ReAct Agent Test - Full Pipeline")
    print("=" * 70)
    print("\nThis test will:")
    print("1. Analyze the URL for form fields (div selection)")
    print("2. Extract bounding boxes from analysis")
    print("3. Use MCP ReAct agent to fill form using screen control tools")
    print("4. Verify results")
    
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print(f"Make sure {url} is open in your browser.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    # Step 1: Analyze
    analysis_result = analyze_form_fields(url, headless)
    
    if not analysis_result.get('fields'):
        print("\n❌ No fields detected. Cannot proceed with filling.")
        return
    
    # Step 2: Use analyze-and-fill endpoint (which uses MCP ReAct agent)
    print("\n" + "=" * 70)
    print("STEP 2: Using MCP ReAct Agent to fill form")
    print("=" * 70)
    print(f"📝 Data to fill: {json.dumps(data, indent=2)}")
    print("\n🤖 Agent will follow ReAct principles:")
    print("   - REASONING: Analyze each field and plan actions")
    print("   - ACTING: Use screen control tools to interact")
    print("   - OBSERVING: Check results after each action")
    print("   - REASONING: Decide next steps based on observations")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auto-fill/analyze-and-fill",
            json={
                "url": url,
                "data": data,
                "headless": headless,
                "screenshot_before": True,
                "screenshot_after": True,
                "delay_between_fields": 0.5
            },
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()
        result = response.json()
        
        # Step 3: Display results
        print("\n" + "=" * 70)
        print("STEP 3: Results")
        print("=" * 70)
        
        print(f"\n✅ Overall Success: {result.get('success', False)}")
        print(f"📝 Message: {result.get('message', 'N/A')}")
        
        if result.get('fill_result'):
            fill_result = result['fill_result']
            print(f"\n📊 Fill Results:")
            print(f"   Success: {fill_result.get('success', False)}")
            print(f"   Filled fields: {fill_result.get('filled_fields', [])}")
            if fill_result.get('failed_fields'):
                print(f"   Failed fields: {fill_result.get('failed_fields', [])}")
            if fill_result.get('errors'):
                print(f"   Errors: {fill_result.get('errors', [])}")
            
            if fill_result.get('screenshot_before'):
                print(f"   📸 Screenshot before: Available (base64)")
            if fill_result.get('screenshot_after'):
                print(f"   📸 Screenshot after: Available (base64)")
        
        if result.get('analysis'):
            analysis = result['analysis']
            print(f"\n📋 Analysis Summary:")
            print(f"   Fields detected: {analysis.get('field_count', 0)}")
            if analysis.get('screenshot_path'):
                print(f"   Screenshot saved: {analysis.get('screenshot_path')}")
        
        # Full result JSON
        print("\n" + "=" * 70)
        print("Full Result JSON:")
        print("=" * 70)
        print(json.dumps(result, indent=2, default=str))
        
        if result.get('success') and result.get('fill_result', {}).get('success'):
            print("\n✅✅✅ SUCCESS: Form was analyzed and filled successfully!")
        else:
            print("\n⚠️  Form filling completed with some issues. Check the results above.")
        
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out!")
        print("The analysis or filling took too long (>5 minutes).")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_mcp_react_agent_direct(fields: List[Dict[str, Any]], data: Dict[str, Any]):
    """
    Test MCP ReAct agent directly with field definitions
    
    Args:
        fields: List of field definitions with bounding boxes
        data: Data to fill into fields
    """
    print("\n" + "=" * 70)
    print("MCP ReAct Agent Test - Direct Field Input")
    print("=" * 70)
    
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure the form is visible on your screen.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print(f"\n📋 Fields to fill: {len(fields)}")
    for field in fields:
        bbox = field.get('bounding_box', {})
        print(f"   - {field.get('id')} ({field.get('field_type')}) at "
              f"({bbox.get('x')}, {bbox.get('y')})")
    
    print(f"\n📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/form-filler/fill",
            json={
                "fields": fields,
                "data": data,
                "screenshot_before": True,
                "screenshot_after": True,
                "delay_between_fields": 0.5
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Filled fields: {result.get('filled_fields', [])}")
        if result.get('failed_fields'):
            print(f"   Failed fields: {result.get('failed_fields', [])}")
        if result.get('errors'):
            print(f"   Errors: {result.get('errors', [])}")
        
        print("\n" + "=" * 70)
        print("Full Result JSON:")
        print("=" * 70)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("The MCP ReAct agent requires an OpenAI API key to work.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    print("=" * 70)
    print("MCP ReAct Agent Test Suite")
    print("=" * 70)
    print("\nChoose test:")
    print("1. Full pipeline: Analyze URL + Fill with MCP ReAct agent (recommended)")
    print("2. Direct test: Fill form with provided field definitions")
    print("3. Two-step: Analyze first, then fill separately")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        # Full pipeline test
        url = input("\nEnter URL to test (default: http://localhost:6767): ").strip()
        if not url:
            url = "http://localhost:6767"
        
        print("\nEnter data to fill (key=value format, one per line, empty line to finish):")
        data = {}
        while True:
            line = input("  > ").strip()
            if not line:
                break
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
        
        if not data:
            # Default data
            data = {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "555-1234"
            }
            print(f"\nUsing default data: {data}")
        
        test_mcp_react_agent_with_analysis(url, data, headless=False)
        
    elif choice == "2":
        # Direct test with field definitions
        print("\nExample field definition:")
        print('{"id": "email", "field_type": "email", "bounding_box": {"x": 500, "y": 300, "width": 250, "height": 35}, "label": "Email"}')
        
        fields_input = input("\nEnter fields JSON (or press Enter for example): ").strip()
        if not fields_input:
            # Example fields
            fields = [
                {
                    "id": "email",
                    "field_type": "email",
                    "bounding_box": {"x": 500, "y": 300, "width": 250, "height": 35},
                    "label": "Email Address"
                },
                {
                    "id": "name",
                    "field_type": "text",
                    "bounding_box": {"x": 500, "y": 250, "width": 250, "height": 35},
                    "label": "Name"
                }
            ]
        else:
            fields = json.loads(fields_input)
        
        data_input = input("\nEnter data JSON (or press Enter for example): ").strip()
        if not data_input:
            data = {"email": "test@example.com", "name": "Test User"}
        else:
            data = json.loads(data_input)
        
        test_mcp_react_agent_direct(fields, data)
        
    elif choice == "3":
        # Two-step test
        url = input("\nEnter URL to analyze (default: http://localhost:6767): ").strip()
        if not url:
            url = "http://localhost:6767"
        
        print("\nStep 1: Analyzing...")
        analysis_result = analyze_form_fields(url, headless=False)
        
        if not analysis_result.get('fields'):
            print("\n❌ No fields detected. Cannot proceed.")
            return
        
        print("\nStep 2: Enter data to fill (key=value format, one per line, empty line to finish):")
        data = {}
        while True:
            line = input("  > ").strip()
            if not line:
                break
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
        
        if not data:
            print("\n⚠️  No data provided. Using empty data dict.")
            data = {}
        
        print("\nStep 3: Filling form with MCP ReAct agent...")
        print("⚠️  WARNING: This will control your mouse and keyboard!")
        print("Press Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
        
        try:
            response = requests.post(
                f"{BASE_URL}/auto-fill/from-analysis",
                json={
                    "analysis_result": analysis_result,
                    "data": data,
                    "screenshot_before": True,
                    "screenshot_after": True,
                    "delay": 0.5
                },
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            
            print("\n✅ Fill Result:")
            print(json.dumps(result, indent=2, default=str))
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

