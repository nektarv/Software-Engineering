import mysql.connector
import csv
from pathlib import Path
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',         
    'password': 'root', 
    'database': 'charging_database'
}

def update_db():
    # Locate prices.csv in the same folder
    csv_path = Path(__file__).parent / "prices.csv"
    
    if not csv_path.exists():
        print("Error: prices.csv file not found.")
        return

    conn = None
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # --- PART 1: Insert/Update New Prices ---
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header row
            
            inserted = 0
            updated = 0

            for row in reader:
                time_str = row[0]
                price_val = float(row[1])

                # Add seconds to match MySQL DATETIME format (YYYY-MM-DD HH:MM:00)
                if len(time_str) == 16:
                    time_str += ":00"

                # 1. Check if record exists
                check_sql = "SELECT price_id FROM dam_prices WHERE timeref = %s LIMIT 1"
                cursor.execute(check_sql, (time_str,))
                existing_record = cursor.fetchone()

                if existing_record:
                    # 2. Update existing record
                    update_sql = "UPDATE dam_prices SET price_eur_per_kwh = %s WHERE price_id = %s"
                    cursor.execute(update_sql, (price_val, existing_record[0]))
                    updated += 1
                else:
                    # 3. Insert new record
                    insert_sql = "INSERT INTO dam_prices (timeref, price_eur_per_kwh, market) VALUES (%s, %s, 'DAM')"
                    cursor.execute(insert_sql, (time_str, price_val))
                    inserted += 1
        
        print(f"Import Finished! Inserted: {inserted}, Updated: {updated}")

        # --- PART 2: Cleanup Old Data ---
        print("Cleaning up old data...")
        
        # Command: Delete everything BEFORE "Yesterday midnight"
        # CURDATE() = Today 00:00
        # INTERVAL 2 DAY = 2 days back (Day before yesterday 00:00)
        # Therefore it keeps: Day before yesterday, Yesterday, Today, Tomorrow.
        cleanup_sql = "DELETE FROM dam_prices WHERE timeref < DATE_SUB(CURDATE(), INTERVAL 2 DAY)"
        
        cursor.execute(cleanup_sql)
        deleted_count = cursor.rowcount
        print(f"Cleanup Done! Deleted {deleted_count} old records.")

        conn.commit()

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    update_db()