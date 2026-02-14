import requests
import json

def test_services_api():
    base_url = "http://localhost:5000"
    
    print("Testing Homy Services API...")
    print("=" * 50)
    
    try:
        # Test main services endpoint
        print("\n1. Testing /api/services...")
        response = requests.get(f"{base_url}/api/services")
        data = response.json()
        
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message', 'No message')}")
        
        if data.get('success'):
            services = data.get('services', [])
            print(f"   Services count: {len(services)}")
            for i, service in enumerate(services[:3], 1):  # Show first 3
                print(f"   Service {i}: {service.get('name')} - KES{service.get('price')}")
        
        # Test clean services endpoint
        print("\n2. Testing /api/services/clean...")
        response = requests.get(f"{base_url}/api/services/clean")
        data = response.json()
        
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message', 'No message')}")
        
        if data.get('success'):
            print(f"   Services count: {data.get('count', 0)}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your Flask app is running on http://localhost:5000")

if __name__ == "__main__":
    test_services_api()