from flask import Flask, render_template, request, jsonify, session as flask_session, redirect, url_for
from flask_cors import CORS
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid
from datetime import datetime, timedelta

from check_db import get_cassandra_session

app = Flask(__name__, static_folder='static')
app.secret_key = 'homy-secret-key-2024'
CORS(app)

# Cassandra connection setup
def create_tables():

    cassandra_session, cluster = get_cassandra_session()
    if cassandra_session:
        # Users table (unchanged)
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY,
                email text,
                password text,
                full_name text,
                phone text,
                created_at timestamp
            )
        """)
        
        # Services table with better structure
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id UUID PRIMARY KEY,
                category text,
                name text,
                description text,
                price decimal,
                duration_minutes int,
                rating float,
                created_at timestamp
            )
        """)
        
        # Create index on category
        cassandra_session.execute("""
            CREATE INDEX IF NOT EXISTS services_category_idx ON services (category)
        """)
        
        # Bookings table (unchanged)
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id UUID PRIMARY KEY,
                user_id UUID,
                service_id UUID,
                booking_date timestamp,
                service_date timestamp,
                address text,
                total_price decimal,
                status text,
                payment_status text
            )
        """)
        
        # Check if services already exist
        result = cassandra_session.execute("SELECT COUNT(*) FROM services")
        if result.one()[0] == 0:
            # Insert sample services only if table is empty
            insert_sample_services(cassandra_session)
        else:
            print(f"Services table already has {result.one()[0]} records")
        
        cluster.shutdown()

# UPDATED: Insert sample services with KES prices
def insert_sample_services(session):
    # First check if services already exist
    result = session.execute("SELECT COUNT(*) FROM services")
    if result.one()[0] > 0:
        print("Services already exist, skipping sample data")
        return
    
    print("Inserting sample services with KES prices...")
    
    # UPDATED: Converted USD to KES (1 USD ≈ 100 KES)
    sample_services = [
        ('AC Repair', 'AC Maintenance', 'Professional AC cleaning and repair', 5000, 60, 4.5),      # was 49.99
        ('Beauty', 'Home Salon', 'Beauty services at home', 4000, 90, 4.7),                          # was 39.99
        ('Plumbing', 'Pipe Fixing', 'Fix leaking pipes and installations', 6000, 45, 4.3),           # was 59.99
        ('Electrician', 'Wiring Repair', 'Electrical repairs and installations', 4500, 60, 4.6),     # was 44.99
        ('Carpentry', 'Furniture Repair', 'Woodwork and furniture services', 5500, 120, 4.4),        # was 54.99
        ('Cleaning', 'Deep Cleaning', 'Complete home cleaning service', 8000, 180, 4.8),              # was 79.99
        ('Washing', 'Laundry Service', 'Pickup and delivery laundry', 3000, 1440, 4.2)                # was 29.99
    ]
    
    for service in sample_services:
        session.execute("""
            INSERT INTO services (service_id, category, name, description, price, duration_minutes, rating, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (uuid.uuid4(), service[0], service[1], service[2], service[3], service[4], service[5], datetime.now()))
    
    print(f"Inserted {len(sample_services)} sample services with KES prices")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services_page():
    return render_template('services.html')

@app.route('/auth')
def auth_page():
    return render_template('auth.html')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

# ============ DB VIEWER ROUTES ============

@app.route('/db-viewer')
def db_viewer():
    """Web interface for database viewing"""
    return render_template('db_viewer.html')

@app.route('/api/db/<table_name>')
def get_table_data(table_name):
    """API endpoint to get table data"""
    if table_name not in ['users', 'services', 'bookings']:
        return jsonify({'success': False, 'message': 'Invalid table name'})
    
    cassandra_session, cluster = get_cassandra_session()
    if not cassandra_session:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        rows = cassandra_session.execute(f"SELECT * FROM {table_name}")
        data = []
        for row in rows:
            row_dict = {}
            for field in row._fields:
                value = getattr(row, field)
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = ''
                else:
                    value = str(value)
                row_dict[field] = value
            data.append(row_dict)
        
        cluster.shutdown()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/db/stats')
def get_db_stats():
    """API endpoint to get database statistics"""
    cassandra_session, cluster = get_cassandra_session()
    if not cassandra_session:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    stats = {}
    
    for table in ['users', 'services', 'bookings']:
        try:
            result = cassandra_session.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = result.one()[0]
        except Exception as e:
            stats[table] = f"Error: {str(e)}"
    
    cluster.shutdown()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/db/sample-data', methods=['POST'])
def create_db_sample_data():
    """API endpoint to create sample data"""
    cassandra_session, cluster = get_cassandra_session()
    if not cassandra_session:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        # Create sample users
        sample_users = [
            (uuid.uuid4(), "john@example.com", "password123", "John Doe", "1234567890", datetime.now()),
            (uuid.uuid4(), "jane@example.com", "password456", "Jane Smith", "0987654321", datetime.now()),
            (uuid.uuid4(), "bob@example.com", "password789", "Bob Wilson", "5551234567", datetime.now())
        ]
        
        for user in sample_users:
            cassandra_session.execute("""
                INSERT INTO users (user_id, email, password, full_name, phone, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, user)
        
        # Create sample bookings with KES prices
        services = cassandra_session.execute("SELECT service_id FROM services LIMIT 3")
        service_ids = [row.service_id for row in services]
        
        if service_ids and sample_users:
            sample_bookings = [
                (uuid.uuid4(), sample_users[0][0], service_ids[0], 
                 datetime.now(), 
                 datetime.now() + timedelta(days=1),
                 "123 Main St, New York", 5000, "confirmed", "paid"),        # was 49.99
                (uuid.uuid4(), sample_users[1][0], service_ids[1], 
                 datetime.now(), 
                 datetime.now() + timedelta(days=2),
                 "456 Oak Ave, Chicago", 4000, "confirmed", "pending"),      # was 39.99
                (uuid.uuid4(), sample_users[2][0], service_ids[2], 
                 datetime.now(), 
                 datetime.now() + timedelta(days=3),
                 "789 Pine Rd, Los Angeles", 6000, "pending", "unpaid")      # was 59.99
            ]
            
            for booking in sample_bookings:
                cassandra_session.execute("""
                    INSERT INTO bookings (booking_id, user_id, service_id, booking_date, 
                                         service_date, address, total_price, status, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, booking)
        
        cluster.shutdown()
        return jsonify({'success': True, 'message': 'Sample data created successfully with KES prices'})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

# ============ END DB VIEWER ROUTES ============

# API Endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    cassandra_session, cluster = get_cassandra_session()
    
    try:
        user_id = uuid.uuid4()
        cassandra_session.execute("""
            INSERT INTO users (user_id, email, password, full_name, phone, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, data['email'], data['password'], data['full_name'], data['phone'], datetime.now()))
        
        cluster.shutdown()
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    cassandra_session, cluster = get_cassandra_session()
    
    try:
        result = cassandra_session.execute("""
            SELECT * FROM users WHERE email = %s AND password = %s ALLOW FILTERING
        """, (data['email'], data['password']))
        
        user = result.one()
        cluster.shutdown()
        
        if user:
            # Use flask_session (not cassandra_session) for user sessions
            flask_session['user_id'] = str(user.user_id)
            flask_session['user_email'] = user.email
            flask_session['user_name'] = user.full_name
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all services - fixed to work with Cassandra"""
    cassandra_session, cluster = get_cassandra_session()
    try:
        # Simple SELECT without DISTINCT (Cassandra doesn't support DISTINCT on non-partition columns)
        result = cassandra_session.execute("SELECT * FROM services")
        
        services = []
        seen_services = set()  # Track unique services client-side
        
        for row in result:
            # Create a unique key for each service to avoid duplicates
            service_key = f"{row.category}-{row.name}-{row.price}"
            
            if service_key not in seen_services:
                seen_services.add(service_key)
                services.append({
                    'id': str(row.service_id),
                    'category': row.category,
                    'name': row.name,
                    'description': row.description,
                    'price': float(row.price),  # Already in KES
                    'duration': row.duration_minutes,
                    'rating': float(row.rating)
                })
        
        cluster.shutdown()
        return jsonify({'success': True, 'services': services})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/book', methods=['POST'])
def book_service():
    data = request.json
    
    # Log the received data for debugging
    print(f"Booking request received: {data}")
    
    cassandra_session, cluster = get_cassandra_session()
    if not cassandra_session:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        # Validate required fields
        required_fields = ['user_id', 'service_id', 'service_date', 'address', 'total_price']
        for field in required_fields:
            if field not in data:
                cluster.shutdown()
                return jsonify({'success': False, 'message': f'Missing required field: {field}'})
        
        # Validate UUIDs
        try:
            user_uuid = uuid.UUID(data['user_id'])
        except ValueError:
            cluster.shutdown()
            return jsonify({'success': False, 'message': f'Invalid user_id format: {data["user_id"]}'})
        
        try:
            service_uuid = uuid.UUID(data['service_id'])
        except ValueError:
            cluster.shutdown()
            return jsonify({'success': False, 'message': f'Invalid service_id format: {data["service_id"]}'})
        
        # Validate service exists
        service_check = cassandra_session.execute(
            "SELECT service_id FROM services WHERE service_id = %s",
            (service_uuid,)
        )
        
        if not service_check.one():
            cluster.shutdown()
            return jsonify({'success': False, 'message': 'Service not found'})
        
        # Parse date
        try:
            # Try multiple date formats
            service_date = None
            date_formats = ['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d']
            
            for date_format in date_formats:
                try:
                    service_date = datetime.strptime(data['service_date'], date_format)
                    break
                except ValueError:
                    continue
            
            if not service_date:
                cluster.shutdown()
                return jsonify({'success': False, 'message': f'Invalid date format: {data["service_date"]}'})
                
        except Exception as e:
            cluster.shutdown()
            return jsonify({'success': False, 'message': f'Date parsing error: {str(e)}'})
        
        # Create booking
        booking_id = uuid.uuid4()
        
        cassandra_session.execute("""
            INSERT INTO bookings (booking_id, user_id, service_id, booking_date, service_date, 
                                 address, total_price, status, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_id,
            user_uuid,
            service_uuid,
            datetime.now(),
            service_date,
            data['address'],
            float(data['total_price']),  # Already in KES
            'confirmed',
            'pending'
        ))
        
        cluster.shutdown()
        return jsonify({
            'success': True, 
            'booking_id': str(booking_id),
            'message': 'Booking confirmed successfully!'
        })
        
    except Exception as e:
        print(f"Booking error details: {str(e)}")
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': f'Booking error: {str(e)}'})

# UPDATED: Fix services table with KES prices
@app.route('/api/fix-services', methods=['POST'])
def fix_services_table():
    """Fix the services table structure and data with KES prices"""
    cassandra_session, cluster = get_cassandra_session()
    
    try:
        # Drop and recreate the services table with proper structure
        cassandra_session.execute("DROP TABLE IF EXISTS services")
        
        # Recreate with better structure
        cassandra_session.execute("""
            CREATE TABLE services (
                service_id UUID PRIMARY KEY,
                category text,
                name text,
                description text,
                price decimal,
                duration_minutes int,
                rating float,
                created_at timestamp
            )
        """)
        
        # Create an index on category for better querying
        cassandra_session.execute("""
            CREATE INDEX IF NOT EXISTS ON services (category)
        """)
        
        # Insert fresh sample data with KES prices
        sample_services = [
            ('AC Repair', 'AC Maintenance', 'Professional AC cleaning and repair', 5000, 60, 4.5),
            ('Beauty', 'Home Salon', 'Beauty services at home', 4000, 90, 4.7),
            ('Plumbing', 'Pipe Fixing', 'Fix leaking pipes and installations', 6000, 45, 4.3),
            ('Electrician', 'Wiring Repair', 'Electrical repairs and installations', 4500, 60, 4.6),
            ('Carpentry', 'Furniture Repair', 'Woodwork and furniture services', 5500, 120, 4.4),
            ('Cleaning', 'Deep Cleaning', 'Complete home cleaning service', 8000, 180, 4.8),
            ('Washing', 'Laundry Service', 'Pickup and delivery laundry', 3000, 1440, 4.2)
        ]
        
        for service in sample_services:
            cassandra_session.execute("""
                INSERT INTO services (service_id, category, name, description, price, duration_minutes, rating, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (uuid.uuid4(), service[0], service[1], service[2], service[3], service[4], service[5], datetime.now()))
        
        # Verify
        result = cassandra_session.execute("SELECT COUNT(*) FROM services")
        count = result.one()[0]
        
        cluster.shutdown()
        return jsonify({
            'success': True, 
            'message': f'Services table recreated with {count} services (KES prices)',
            'count': count
        })
        
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

# UPDATED: Debug endpoint to show KES prices
@app.route('/api/debug/services', methods=['GET'])
def debug_services():
    """Debug endpoint to check service UUIDs and KES prices"""
    cassandra_session, cluster = get_cassandra_session()
    try:
        result = cassandra_session.execute("SELECT service_id, name, price FROM services")
        services = []
        for row in result:
            services.append({
                'service_id': str(row.service_id),
                'service_id_raw': row.service_id.hex if hasattr(row.service_id, 'hex') else str(row.service_id),
                'name': row.name,
                'price_KES': float(row.price)
            })
        cluster.shutdown()
        return jsonify({'success': True, 'services': services})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

# Additional API endpoint for checking user sessions
@app.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in flask_session:
        return jsonify({
            'logged_in': True, 
            'user_id': flask_session['user_id'],
            'email': flask_session.get('user_email', ''),
            'name': flask_session.get('user_name', '')
        })
    return jsonify({'logged_in': False})

# Logout endpoint
@app.route('/api/logout', methods=['POST'])
def logout():
    flask_session.pop('user_id', None)
    flask_session.pop('user_email', None)
    flask_session.pop('user_name', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Get current user bookings
@app.route('/api/my-bookings', methods=['GET'])
def get_my_bookings():
    if 'user_id' not in flask_session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    cassandra_session, cluster = get_cassandra_session()
    try:
        user_id = uuid.UUID(flask_session['user_id'])
        result = cassandra_session.execute("""
            SELECT * FROM bookings WHERE user_id = %s ALLOW FILTERING
        """, (user_id,))
        
        bookings = []
        for row in result:
            bookings.append({
                'booking_id': str(row.booking_id),
                'service_id': str(row.service_id),
                'booking_date': row.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
                'service_date': row.service_date.strftime('%Y-%m-%d %H:%M:%S'),
                'address': row.address,
                'total_price': float(row.total_price),  # Already in KES
                'status': row.status,
                'payment_status': row.payment_status
            })
        
        cluster.shutdown()
        return jsonify({'success': True, 'bookings': bookings})
    except Exception as e:
        if cluster:
            cluster.shutdown()
        return jsonify({'success': False, 'message': str(e)})

# UPDATED: Add a convenience endpoint to get KES conversion rate
@app.route('/api/currency', methods=['GET'])
def get_currency():
    """Get currency information"""
    return jsonify({
        'success': True,
        'currency': 'KES',
        'symbol': 'KES',
        'convenience_fee': 300,
        'conversion_rate': '1 USD ≈ 100 KES'
    })

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)