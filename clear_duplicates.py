from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid

def clear_duplicates():
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
    cluster = Cluster(['127.0.0.1'], auth_provider=auth_provider)
    session = cluster.connect('homy')
    
    # Clear all tables
    session.execute("TRUNCATE services")
    session.execute("TRUNCATE users")
    session.execute("TRUNCATE bookings")
    
    print("All tables cleared. Restart your Flask app to recreate sample data.")
    
    cluster.shutdown()

if __name__ == "__main__":
    clear_duplicates()