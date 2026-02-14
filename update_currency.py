from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime

def update_prices_to_kes():
    """Convert existing dollar prices to KES (approximate conversion)"""
    print("🔗 Connecting to Cassandra database...")
    
    try:
        auth_provider = PlainTextAuthProvider(
            username='cassandra', 
            password='cassandra'
        )
        cluster = Cluster(['127.0.0.1'], auth_provider=auth_provider)
        session = cluster.connect('homy')
        
        print("✅ Connected to database")
        
        # 1. Update services table
        print("\n📊 Updating services table...")
        services = session.execute("SELECT service_id, price FROM services")
        
        service_count = 0
        for service in services:
            # Convert USD to KES (1 USD ≈ 100 KES)
            old_price = float(service.price)
            new_price = old_price * 100
            
            session.execute("""
                UPDATE services SET price = %s WHERE service_id = %s
            """, (new_price, service.service_id))
            
            service_count += 1
            print(f"  • Service {service.service_id}: KES {new_price:.2f} (was ${old_price:.2f})")
        
        # 2. Update bookings table
        print("\n📊 Updating bookings table...")
        bookings = session.execute("SELECT booking_id, total_price FROM bookings")
        
        booking_count = 0
        for booking in bookings:
            old_price = float(booking.total_price)
            new_price = old_price * 100
            
            session.execute("""
                UPDATE bookings SET total_price = %s WHERE booking_id = %s
            """, (new_price, booking.booking_id))
            
            booking_count += 1
            print(f"  • Booking {booking.booking_id}: KES {new_price:.2f}")
        
        print(f"\n✅ Update complete!")
        print(f"   • Updated {service_count} services")
        print(f"   • Updated {booking_count} bookings")
        print(f"   • Conversion rate used: 1 USD = 100 KES")
        
        cluster.shutdown()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_prices_to_kes()