import requests
import json

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

def test_api():
    base_url = "https://localhost:9876"
    
    tests = [
        ("Root", "GET", "/"),
        ("Points list", "GET", "/api/points"),
        ("Point 5", "GET", "/api/point/5"),
        ("Reserve point 5", "POST", "/api/reserve/5/45", {}),
        ("Update point 5", "POST", "/api/updpoint/5", {"status": "available", "kwhprice": 0.40}),
    ]
    
    for name, method, path, *data in tests:
        url = f"{base_url}{path}"
        try:
            if method == "POST":
                response = requests.post(url, json=data[0] if data else {}, verify=False)
            else:
                response = requests.get(url, verify=False)
            
            status = "✅" if response.status_code in [200, 204] else "❌"
            print(f"{status} {name}: {response.status_code}")
            
            if response.text:
                try:
                    print(f"   Response: {json.dumps(response.json(), indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
            print()
        except Exception as e:
            print(f"❌ {name}: {e}\n")

if __name__ == "__main__":
    print("Testing HTTPS API...\n")
    test_api()