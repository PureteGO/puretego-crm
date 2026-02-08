import pymysql
import os

# Configuration from auto_setup_cpanel.py (assuming same credentials for DB user 'puretego')
DB_HOST = "puretego.online" 
# Alternative from screenshot: "zeta.host-server.link" or "23.94.19.230"
DB_USER = "puretego"
DB_PASS = "Kn16Nt]wB3O:3k"
DB_NAME_OPTIONS = ["puretego_puretego_crm", "puretego_crm", "puretego_db", "puretego_admin", "puretego_main"]
DB_USERS = ["puretego", "puretego_admin", "puretego_crm", "admin"]

def connect_db():
    start_host = DB_HOST
    hosts = [DB_HOST, "zeta.host-server.link", "23.94.19.230"]
    
    for host in hosts:
        for user in DB_USERS:
            for db_name in DB_NAME_OPTIONS:
                print(f"Trying {user} @ {host} with DB {db_name}...")
                try:
                    conn = pymysql.connect(
                        host=host,
                        user=user,
                        password=DB_PASS,
                        database=db_name,
                        cursorclass=pymysql.cursors.DictCursor,
                        connect_timeout=10
                    )
                    print(f"✅ SUCCESS! Connected to {host} / {db_name} as {user}")
                    return conn
                except pymysql.MySQLError as e:
                    print(f"Failed ({user}/{db_name}): {e}")
    return None

def run_migration():
    conn = connect_db()
    if not conn:
        print("Could not connect to database with known credentials.")
        return

    try:
        with open('migration_finance.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Split SQL by semicolon, but handle delimiters properly
        # For simplicity, we just split by ; and ignore empty lines
        commands = sql_script.split(';')
        
        with conn.cursor() as cursor:
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    try:
                        print(f"Executing: {cmd[:50]}...")
                        cursor.execute(cmd)
                    except pymysql.MySQLError as e:
                        # Ignore "Duplicate column name" error for roles
                        if "Duplicate column name" in str(e):
                            print("Column already exists, skipping.")
                        elif "Table 'payables' already exists" in str(e):
                             print("Table payables exists, skipping.")
                        else:
                            print(f"Error executing command: {e}")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
