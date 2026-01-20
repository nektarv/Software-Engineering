import mysql.connector
import csv
from pathlib import Path

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

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header row ("datetime_athens", "eur_per_kwh")
            
            inserted = 0
            updated = 0

            for row in reader:
                # CSV format: YYYY-MM-DD HH:MM
                time_str = row[0]
                price_val = float(row[1])

                # Add seconds to match MySQL DATETIME format (YYYY-MM-DD HH:MM:00)
                if len(time_str) == 16:
                    time_str += ":00"

                # 1. Check if record exists for this time
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

        conn.commit()
        print(f"Done! Inserted: {inserted}, Updated: {updated}")

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