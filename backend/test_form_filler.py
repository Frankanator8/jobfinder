#!/usr/bin/env python3
"""
Test script for form filling agent

Usage:
    python test_form_filler.py

Make sure:
1. The FastAPI server is running: uvicorn app.main:app --reload
2. You have OPENAI_API_KEY set in your environment
3. You have a form visible on your screen
"""
import os
import requests
import json

BASE_URL = "http://localhost:8000/form-filler"

def test_simple_form_fill():
    """Test filling a simple form"""
    print("=" * 60)
    print("Testing Form Filler Agent")
    print("=" * 60)
    
    # Example: Fill out a simple login form
    # Adjust these coordinates to match a form on your screen
    fields = [
        {
            "id": "username",
            "field_type": "text",
            "x": 500,  # Adjust to your form's username field
            "y": 300,
            "width": 200,
            "height": 30,
            "label": "Username"
        },
        {
            "id": "password",
            "field_type": "password",
            "x": 500,  # Adjust to your form's password field
            "y": 350,
            "width": 200,
            "height": 30,
            "label": "Password"
        },
        {
            "id": "submit",
            "field_type": "button",
            "x": 500,  # Adjust to your form's submit button
            "y": 400,
            "width": 100,
            "height": 40,
            "label": "Submit"
        }
    ]
    
    data = {
        "username": "testuser",
        "password": "testpass123",
    }
    
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure you have a form visible on your screen.")
    print("Adjust the field coordinates in the script to match your form.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print("\n📝 Fields to fill:")
    for field in fields:
        print(f"  - {field['label']} ({field['field_type']}) at ({field['x']}, {field['y']})")
    
    print("\n📊 Data to fill:")
    for key, value in data.items():
        print(f"  - {key}: {value}")
    
    print("\n🚀 Sending request to agent...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/fill-simple",
            json={
                "fields": fields,
                "data": data,
                "delay": 0.5
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Result:")
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            print("\n✅ Form filled successfully!")
        else:
            print("\n⚠️  Some fields may have failed:")
            if result.get("failed_fields"):
                print(f"  Failed: {result['failed_fields']}")
            if result.get("errors"):
                print(f"  Errors: {result['errors']}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_advanced_form_fill():
    """Test with the full FormFieldsRequest schema"""
    print("\n" + "=" * 60)
    print("Testing Advanced Form Fill")
    print("=" * 60)
    
    # Example with full schema
    request_data = {
        "fields": [
            {
                "id": "email",
                "field_type": "email",
                "bounding_box": {
                    "x": 500,
                    "y": 300,
                    "width": 250,
                    "height": 35
                },
                "label": "Email Address",
                "required": True
            },
            {
                "id": "country",
                "field_type": "dropdown",
                "bounding_box": {
                    "x": 500,
                    "y": 350,
                    "width": 250,
                    "height": 35
                },
                "label": "Country",
                "options": ["USA", "Canada", "UK", "Australia"],
                "required": True
            },
            {
                "id": "newsletter",
                "field_type": "checkbox",
                "bounding_box": {
                    "x": 500,
                    "y": 400,
                    "width": 20,
                    "height": 20
                },
                "label": "Subscribe to newsletter",
                "required": False
            }
        ],
        "data": {
            "email": "user@example.com",
            "country": "USA",
            "newsletter": "true"
        },
        "screenshot_before": True,
        "screenshot_after": True,
        "delay_between_fields": 0.5
    }
    
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure you have a form visible on your screen.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print("\n🚀 Sending request to agent...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/fill",
            json=request_data
        )
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Result:")
        print(f"Success: {result.get('success')}")
        print(f"Filled fields: {result.get('filled_fields')}")
        print(f"Failed fields: {result.get('failed_fields')}")
        if result.get("errors"):
            print(f"Errors: {result.get('errors')}")
        
        if result.get("screenshot_before"):
            print("\n📸 Screenshot before taken (base64 data available)")
        if result.get("screenshot_after"):
            print("📸 Screenshot after taken (base64 data available)")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("The agent requires an OpenAI API key to work.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    print("Choose test:")
    print("1. Simple form fill")
    print("2. Advanced form fill")
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_simple_form_fill()
    elif choice == "2":
        test_advanced_form_fill()
    else:
        print("Invalid choice")

