#!/usr/bin/env python3
"""
Simple test script for Screen Control API

Usage:
    python test_screen_control.py

Make sure the FastAPI server is running first:
    uvicorn app.main:app --reload
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/screen-control"

def test_screen_info():
    """Test getting screen information"""
    print("\n📺 Testing: Get Screen Info")
    response = requests.get(f"{BASE_URL}/info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mouse_position():
    """Test getting mouse position"""
    print("\n🖱️  Testing: Get Mouse Position")
    response = requests.get(f"{BASE_URL}/mouse/position")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mouse_move(x, y, duration=0.5):
    """Test moving mouse"""
    print(f"\n🖱️  Testing: Move Mouse to ({x}, {y})")
    payload = {"x": x, "y": y, "duration": duration}
    response = requests.post(f"{BASE_URL}/mouse/move", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mouse_click(x, y, button="left", clicks=1):
    """Test clicking mouse"""
    print(f"\n🖱️  Testing: Click Mouse at ({x}, {y})")
    payload = {"x": x, "y": y, "button": button, "clicks": clicks}
    response = requests.post(f"{BASE_URL}/mouse/click", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_screenshot_base64():
    """Test taking screenshot (base64)"""
    print("\n📸 Testing: Take Screenshot (Base64)")
    response = requests.get(f"{BASE_URL}/screenshot/base64")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Image size: {len(data.get('image', ''))} characters")
    print(f"Format: {data.get('format')}")
    return data

def test_keyboard_press(keys="ctrl+c"):
    """Test pressing keyboard keys"""
    print(f"\n⌨️  Testing: Press Keys '{keys}'")
    payload = {"keys": keys, "presses": 1}
    response = requests.post(f"{BASE_URL}/keyboard/press", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_keyboard_type(text="Hello from API!"):
    """Test typing text"""
    print(f"\n⌨️  Testing: Type Text '{text}'")
    response = requests.post(f"{BASE_URL}/keyboard/type", params={"text": text})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mouse_scroll(clicks=3):
    """Test scrolling"""
    print(f"\n🖱️  Testing: Scroll {clicks} clicks")
    payload = {"clicks": clicks, "horizontal": False}
    response = requests.post(f"{BASE_URL}/mouse/scroll", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def main():
    """Run all tests"""
    print("=" * 60)
    print("Screen Control API Test Script")
    print("=" * 60)
    print("\n⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure you're ready and the server is running.")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    try:
        # Test 1: Get screen info
        screen_info = test_screen_info()
        screen_width = screen_info["width"]
        screen_height = screen_info["height"]
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # Test 2: Get mouse position
        test_mouse_position()
        
        # Test 3: Move mouse to center (slowly)
        print("\n⏳ Moving mouse to center in 2 seconds...")
        time.sleep(2)
        test_mouse_move(center_x, center_y, duration=1.0)
        
        # Test 4: Take screenshot
        test_screenshot_base64()
        
        # Test 5: Scroll
        print("\n⏳ Scrolling in 2 seconds...")
        time.sleep(2)
        test_mouse_scroll(3)
        
        # Test 6: Keyboard press (Ctrl+C - safe, just copies if something is selected)
        print("\n⏳ Pressing Ctrl+C in 2 seconds...")
        time.sleep(2)
        test_keyboard_press("ctrl+c")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\n💡 Tip: Open http://localhost:8000/docs for interactive API testing")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server!")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

