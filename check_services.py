from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

def check_services():
    try:
        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
        cluster = Cluster(['127.0.0.1'], auth_provider=auth_provider)
        session = cluster.connect('homy')
        
        # Check services table
        result = session.execute("SELECT * FROM services")
        services = list(result)
        
        print(f"Found {len(services)} services in database:")
        print("-" * 80)
        
        for i, service in enumerate(services, 1):
            print(f"\nService {i}:")
            print(f"  ID: {service.service_id}")
            print(f"  Name: {service.name}")
            print(f"  Category: {service.category}")
            print(f"  Price: KES{service.price}")
            print(f"  Description: {service.description}")
        
        cluster.shutdown()
        
        if len(services) == 0:
            print("\n⚠️  No services found in database!")
            print("Restart your Flask app to create sample services.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_services()