"""
URL Verification Script for Finucity
Tests all available routes and displays their status
Run this after starting the server
"""

import requests
import sys

# Base URL
BASE_URL = "http://localhost:3000"

# All available URLs to test
URLS = {
    "Main & Public": [
        ("/", "Homepage"),
        ("/about", "About Page"),
        ("/faq", "FAQ Page"),
    ],
    
    "Authentication (No login required)": [
        ("/auth/gateway", "Auth Gateway"),
        ("/auth/login", "Login Page"),
        ("/auth/register", "Register Page"),
    ],
    
    "User Dashboard (Login required)": [
        ("/user/dashboard", "User Dashboard"),
        ("/user/find-ca", "Find CA"),
        ("/profile", "User Profile"),
    ],
    
    "AI Chat (Login required)": [
        ("/chat", "AI Chat Interface"),
    ],
    
    "CA Routes (CA access required)": [
        ("/ca/dashboard", "CA Dashboard"),
        ("/ca-application", "CA Application Form"),
        ("/ca-application-status", "Application Status"),
        ("/test-ca-dashboard", "Test CA Dashboard (shortcut)"),
    ],
    
    "Admin Panel (Admin access required)": [
        ("/admin", "Admin Shortcut"),
        ("/admin/dashboard", "Admin Dashboard"),
        ("/admin/users", "User Management"),
        ("/admin/ca-applications", "CA Applications Review"),
        ("/admin/login", "Admin Login"),
    ],
    
    "API Endpoints (Authenticated)": [
        ("/api/admin/ca-applications", "Get CA Applications (Admin)"),
    ],
}

def test_url(url, description):
    """Test a URL and return its status."""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5, allow_redirects=False)
        status_code = response.status_code
        
        if status_code == 200:
            status = "OK"
            symbol = "✅"
        elif status_code in [301, 302, 303, 307, 308]:
            redirect_to = response.headers.get('Location', 'Unknown')
            status = f"REDIRECT → {redirect_to}"
            symbol = "🔀"
        elif status_code == 401:
            status = "AUTH REQUIRED (Login needed)"
            symbol = "🔒"
        elif status_code == 403:
            status = "FORBIDDEN (Higher permissions needed)"
            symbol = "🚫"
        elif status_code == 404:
            status = "NOT FOUND"
            symbol = "❌"
        elif status_code == 500:
            status = "SERVER ERROR"
            symbol = "💥"
        else:
            status = f"{status_code}"
            symbol = "ℹ️"
            
        return status_code, symbol, status
    except requests.exceptions.ConnectionError:
        return None, "❌", "CONNECTION FAILED (Server not running?)"
    except requests.exceptions.Timeout:
        return None, "⏱️", "TIMEOUT"
    except Exception as e:
        return None, "❌", f"ERROR: {str(e)}"

def main():
    """Test all URLs and display results."""
    print()
    print("=" * 80)
    print("🧪 FINUCITY URL VERIFICATION TEST")
    print("=" * 80)
    print()
    print(f"Testing server at: {BASE_URL}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=3)
        print("✅ Server is running!")
    except:
        print("❌ Server is NOT running. Please start the app first:")
        print("   python app.py")
        print()
        return
    
    print()
    print("-" * 80)
    
    # Test all URLs by category
    total_tested = 0
    total_ok = 0
    total_redirect = 0
    total_auth_required = 0
    total_errors = 0
    
    for category, urls in URLS.items():
        print()
        print(f"📂 {category}")
        print("-" * 80)
        
        for url, description in urls:
            status_code, symbol, status = test_url(url, description)
            total_tested += 1
            
            # Update counters
            if status_code == 200:
                total_ok += 1
            elif status_code in [301, 302, 303, 307, 308]:
                total_redirect += 1
            elif status_code in [401, 403]:
                total_auth_required += 1
            elif status_code is None or status_code >= 400:
                total_errors += 1
            
            # Print result
            print(f"  {symbol} {url:40} {description:30} {status}")
    
    # Summary
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()
    print(f"  Total URLs Tested: {total_tested}")
    print(f"  ✅ Working (200): {total_ok}")
    print(f"  🔀 Redirects: {total_redirect}")
    print(f"  🔒 Auth Required: {total_auth_required}")
    print(f"  ❌ Errors/Not Found: {total_errors}")
    print()
    
    # Quick access URLs
    print("=" * 80)
    print("🚀 QUICK ACCESS URLS")
    print("=" * 80)
    print()
    print(f"  Main App:           {BASE_URL}")
    print(f"  Test CA Dashboard:  {BASE_URL}/test-ca-dashboard")
    print(f"  Apply as CA:        {BASE_URL}/ca-application")
    print(f"  Admin Panel:        {BASE_URL}/admin")
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    try:
        import requests
        main()
    except ImportError:
        print("\n❌ Error: 'requests' module not found.")
        print("Install it with: pip install requests\n")
        sys.exit(1)
