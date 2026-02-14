from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import sys
import json
from datetime import datetime
import uuid

def get_cassandra_session():
    """Establish connection to Cassandra"""
    try:
        auth_provider = PlainTextAuthProvider(
            username='cassandra', 
            password='cassandra'
        )
        cluster = Cluster(['127.0.0.1'], auth_provider=auth_provider)
        session = cluster.connect('homy')
        return session, cluster
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}")
        return None, None

def print_table_clean(session, table_name):
    """Clean table display without external libraries"""
    try:
        rows = list(session.execute(f"SELECT * FROM {table_name}"))
        
        if not rows:
            print(f"\n📭 Table '{table_name}' is empty")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 TABLE: {table_name.upper()} ({len(rows)} rows)")
        print('='*80)
        
        for i, row in enumerate(rows, 1):
            print(f"\n📍 RECORD {i}:")
            print('-' * 40)
            
            for field in row._fields:
                value = getattr(row, field)
                
                # Format the value
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                elif value is None:
                    value = "[NULL]"
                elif isinstance(value, float):
                    value = f"{value:.2f}"
                else:
                    value = str(value)
                
                # Truncate very long values
                if len(value) > 50:
                    value = value[:47] + "..."
                
                # Display field name (human readable) and value
                field_name = field.replace('_', ' ').title()
                print(f"  {field_name:20}: {value}")
        
        print(f"\n{'='*80}")
        print(f"✅ Displayed {len(rows)} records from '{table_name}'")
        print('='*80)
        
    except Exception as e:
        print(f"❌ Error reading table '{table_name}': {e}")

def print_table_summary(session, table_name):
    """Show summary view of table (first 3 rows)"""
    try:
        rows = list(session.execute(f"SELECT * FROM {table_name} LIMIT 3"))
        
        if not rows:
            print(f"\n📭 Table '{table_name}' is empty")
            return
        
        total_count = session.execute(f"SELECT COUNT(*) FROM {table_name}").one()[0]
        
        print(f"\n{'='*60}")
        print(f"📋 TABLE SUMMARY: {table_name.upper()}")
        print(f"📊 Total Records: {total_count}")
        print(f"👀 Showing first {min(3, len(rows))} records")
        print('='*60)
        
        columns = list(rows[0]._fields)
        
        # Print column headers
        print("\nCOLUMNS:")
        for col in columns:
            print(f"  • {col}")
        
        print("\nSAMPLE DATA:")
        for i, row in enumerate(rows, 1):
            print(f"\n  Record {i}:")
            for col in columns:
                value = getattr(row, col)
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M')
                elif isinstance(value, uuid.UUID):
                    value = str(value)[:8] + "..."
                elif value is None:
                    value = "[NULL]"
                else:
                    value = str(value)[:30] + ("..." if len(str(value)) > 30 else "")
                
                print(f"    {col:20} = {value}")
        
        if total_count > 3:
            print(f"\n⚠️  ... and {total_count - 3} more records not shown")
        
        print('='*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def export_table_to_json(session, table_name, filename=None):
    """Export table data to JSON file"""
    if not filename:
        filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        rows = list(session.execute(f"SELECT * FROM {table_name}"))
        
        data = []
        for row in rows:
            record = {}
            for field in row._fields:
                value = getattr(row, field)
                
                # Convert special types for JSON
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                elif hasattr(value, '__dict__'):
                    value = str(value)
                
                record[field] = value
            data.append(record)
        
        with open(filename, 'w') as f:
            json.dump({
                'table': table_name,
                'export_date': datetime.now().isoformat(),
                'record_count': len(data),
                'data': data
            }, f, indent=2, default=str)
        
        print(f"✅ Exported {len(data)} records to '{filename}'")
        return filename
        
    except Exception as e:
        print(f"❌ Export error: {e}")
        return None

def show_table_schema(session, table_name):
    """Show table schema information"""
    try:
        # Get schema info from system tables
        result = session.execute("""
            SELECT column_name, type, kind 
            FROM system_schema.columns 
            WHERE keyspace_name = 'homy' AND table_name = %s
            ORDER BY position
        """, (table_name,))
        
        columns = list(result)
        
        if not columns:
            print(f"❌ No schema found for table '{table_name}'")
            return
        
        print(f"\n{'='*60}")
        print(f"🗺️  SCHEMA: {table_name.upper()}")
        print('='*60)
        
        print("\nCOLUMNS:")
        for col in columns:
            print(f"  • {col.column_name:20} : {col.type:15} ({col.kind})")
        
        # Get primary key info
        result = session.execute("""
            SELECT column_name, type 
            FROM system_schema.columns 
            WHERE keyspace_name = 'homy' AND table_name = %s AND kind = 'partition_key'
        """, (table_name,))
        
        pk_columns = list(result)
        if pk_columns:
            print(f"\n🔑 PRIMARY KEY: {', '.join([col.column_name for col in pk_columns])}")
        
        # Get table size estimate
        try:
            count = session.execute(f"SELECT COUNT(*) FROM {table_name}").one()[0]
            print(f"\n📊 ESTIMATED SIZE: {count} records")
        except:
            pass
        
        print('='*60)
        
    except Exception as e:
        print(f"❌ Schema error: {e}")

def show_database_info(session):
    """Show database information"""
    try:
        # Get all tables
        result = session.execute("""
            SELECT table_name 
            FROM system_schema.tables 
            WHERE keyspace_name = 'homy'
            ORDER BY table_name
        """)
        
        tables = [row.table_name for row in result]
        
        print(f"\n{'='*60}")
        print("🗄️  DATABASE: HOMY")
        print('='*60)
        
        print(f"\n📋 TABLES ({len(tables)}):")
        for table in tables:
            try:
                count = session.execute(f"SELECT COUNT(*) FROM {table}").one()[0]
                print(f"  • {table:20} : {count:5} records")
            except:
                print(f"  • {table:20} : [ERROR]")
        
        # Get Cassandra version
        try:
            version = session.execute("SELECT release_version FROM system.local").one().release_version
            print(f"\n⚙️  CASSANDRA VERSION: {version}")
        except:
            pass
        
        print('='*60)
        
    except Exception as e:
        print(f"❌ Database info error: {e}")

def show_menu():
    """Display menu options"""
    print("\n" + "="*60)
    print("🎯 HOMY DATABASE MANAGEMENT TOOL")
    print("="*60)
    print("1. View all tables (detailed)")
    print("2. View all tables (summary)")
    print("3. View users table")
    print("4. View services table")
    print("5. View bookings table")
    print("6. Show table schemas")
    print("7. Export table to JSON")
    print("8. Show database information")
    print("9. Fix services table")
    print("0. Exit")
    print("-"*60)

def fix_services_table(session):
    """Recreate services table with sample data"""
    print("\n⚠️  WARNING: This will delete all services and recreate them!")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        return
    
    try:
        # Drop and recreate table
        session.execute("DROP TABLE IF EXISTS services")
        
        session.execute("""
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
        
        # Create index
        session.execute("CREATE INDEX IF NOT EXISTS ON services (category)")
        
        # UPDATED: Insert sample data with KES prices
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
            session.execute("""
                INSERT INTO services (service_id, category, name, description, price, duration_minutes, rating, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (uuid.uuid4(), service[0], service[1], service[2], service[3], service[4], service[5], datetime.now()))
        
        count = session.execute("SELECT COUNT(*) FROM services").one()[0]
        print(f"✅ Services table recreated with {count} sample services (KES prices)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🔗 Connecting to Cassandra database...")
    session, cluster = get_cassandra_session()
    
    if not session:
        print("❌ Failed to connect to Cassandra. Make sure Cassandra is running.")
        sys.exit(1)
    
    print("✅ Connected to Cassandra database 'homy'")
    
    while True:
        show_menu()
        choice = input("\nSelect an option (0-9): ").strip()
        
        if choice == '0':
            print("👋 Exiting...")
            break
        
        elif choice == '1':
            print("\n📋 Viewing all tables (detailed):")
            for table in ['users', 'services', 'bookings']:
                print_table_clean(session, table)
        
        elif choice == '2':
            print("\n📋 Viewing all tables (summary):")
            for table in ['users', 'services', 'bookings']:
                print_table_summary(session, table)
        
        elif choice == '3':
            print_table_clean(session, 'users')
        
        elif choice == '4':
            print_table_clean(session, 'services')
        
        elif choice == '5':
            print_table_clean(session, 'bookings')
        
        elif choice == '6':
            print("\n🗺️  Table Schemas:")
            for table in ['users', 'services', 'bookings']:
                show_table_schema(session, table)
        
        elif choice == '7':
            table = input("Enter table name to export (users/services/bookings): ").strip()
            if table in ['users', 'services', 'bookings']:
                export_table_to_json(session, table)
            else:
                print("❌ Invalid table name")
        
        elif choice == '8':
            show_database_info(session)
        
        elif choice == '9':
            fix_services_table(session)
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")
    
    # Cleanup
    if cluster:
        cluster.shutdown()
    print("✅ Connection closed")

if __name__ == "__main__":
    main()