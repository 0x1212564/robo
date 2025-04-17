import mysql.connector
from mysql.connector import Error

class DatabaseWrapper:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Successfully connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
            
    def get_open_orders(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM orders WHERE status = 'open'"
            cursor.execute(query)
            orders = cursor.fetchall()
            cursor.close()
            return orders
            
        except Error as e:
            print(f"Error retrieving open orders: {e}")
            return []
