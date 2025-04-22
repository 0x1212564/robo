import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host='localhost',          # Replace with your host
            database='restaurant',  # Replace with your database name
            user='root',      # Replace with your username
            password='64mz8nkb',   # Replace with your password
            auth_plugin='mysql_native_password'
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for named columns
            
            # Query to get new orders
            query = "SELECT * FROM bestelling WHERE status = 'nieuw'"
            cursor.execute(query)
            
            # Fetch all new orders
            new_orders = cursor.fetchall()
            
            return new_orders

    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# Example usage
if __name__ == "__main__":
    orders = connect_to_database()
    if orders:
        print(f"Found {len(orders)} new orders:")
        for i, order in enumerate(orders, 1):
            print(f"\n--- Order #{i} ---")
            for key, value in order.items():
                print(f"{key}: {value}")
    else:
        print("No new orders found or could not connect to database.")
