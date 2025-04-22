from pyfirmata2 import Arduino, util
import time
from database_wrapper import DatabaseWrapper

# Board setup
board = Arduino('COM4')
it = util.Iterator(board)
it.start()
time.sleep(1)

# Motor pins setup
motor_left = board.get_pin("d:11:p")
motor_right = board.get_pin("d:3:p")

# Dictionary for sensor values
sensor_values = {}

# Move history stack to track decisions
move_history = []
# Maximum size for the move history stack
MAX_HISTORY_SIZE = 10

# Database setup
db = DatabaseWrapper(host="localhost", user="root", password="password", database="robot_db")
db.connect()
# Variable to store open orders
open_orders = []
# Time tracking for database updates
last_db_update = time.time()
DB_UPDATE_INTERVAL = 10  # Update every 10 seconds

# Callback factory for sensors
def create_callback(sensor_name):
    def callback(value):
        sensor_values[sensor_name] = value
    return callback

def set_motor_speed(left_speed, right_speed):
    motor_left.write(left_speed)
    motor_right.write(right_speed)

def determine_direction(sensors):
    """
    Determine direction based on sensor readings
    
    Args:
        sensors (list): List of 5 sensor readings (0 or 1)
        
    Returns:
        str: Direction command ("Rechtdoor", "Links", "Rechts", "T-Intersection", or "Machine Stop")
    """
    # Convert sensor readings to tuple for easier pattern matching
    s = tuple(sensors)
    
    # Check for overshoot (all sensors on white)
    if s == (1, 1, 1, 1, 1):
        # Overshoot detected, use last significant decision if available
        for last_move in reversed(move_history):
            if last_move in ["Links", "Rechts"]:
                return last_move
        # If no turns in history, default to straight
        return "Rechtdoor"
    
    # Define T-intersection patterns
    t_intersection_patterns = [
        (0, 0, 0, 0, 0),  # All sensors on black (complete T)
        (0, 0, 1, 0, 0),  # Middle on line with both sides triggering
        (0, 1, 0, 0, 0),  # Left side strongly triggering
        (0, 0, 0, 1, 0),  # Right side strongly triggering
        (0, 1, 0, 1, 0),  # Both sides triggering symmetrically
        (0, 0, 1, 0, 0),  # Middle sensor on line with both sides dark
    ]
    
    # Define direction patterns
    rechtdoor_patterns = [
        (1, 1, 0, 1, 1),  # Middle sensor on black
        (0, 1, 1, 1, 0),  # Two outer sensors on black
        (0, 1, 1, 0, 0),  # Two outer right and center on black
        (0, 0, 1, 1, 0),  # Two outer left and center on black
        (0, 1, 0, 1, 1),  # Middle and outer left on black
        (1, 1, 0, 1, 0),  # Middle and outer right on black
        (1, 0, 0, 0, 1),  # Outer sensors on black
        (0, 1, 0, 0, 1),  # Outer right and inner left on black
        (1, 0, 1, 0, 0),  # Inner left and middle on black
        (0, 0, 1, 0, 1),  # Inner right and middle on black
    ]
    
    links_patterns = [
        (1, 0, 1, 1, 1),  # Left sensor on black
        (0, 1, 1, 1, 1),  # Left-most sensor on black
        (1, 0, 0, 1, 1),  # Middle and left sensor on black
        (0, 0, 0, 1, 1),  # Middle, left and left-most sensor on black
        (0, 0, 0, 0, 1),  # 4 left sensors on black
        (0, 0, 1, 1, 1),  # 2 left sensors on black
    ]
    
    rechts_patterns = [
        (1, 1, 1, 0, 1),  # Right sensor on black
        (1, 1, 1, 1, 0),  # Right-most sensor on black
        (1, 1, 0, 0, 1),  # Middle and right sensor on black
        (1, 1, 0, 0, 0),  # Middle, right and right-most sensor on black
        (1, 0, 0, 0, 0),  # 4 right sensors on black
        (1, 1, 1, 0, 0),  # 2 right sensors on black
    ]
    
    # First check for T-intersection
    if s in t_intersection_patterns:
        return "T-Intersection"
    # Then check other patterns
    elif s in rechtdoor_patterns:
        return "Rechtdoor"
    elif s in links_patterns:
        return "Links"
    elif s in rechts_patterns:
        return "Rechts"
    else:
        return "Machine Stop"
    """
    Determine direction based on sensor readings
    
    Args:
        sensors (list): List of 5 sensor readings (0 or 1)
        
    Returns:
        str: Direction command ("Rechtdoor", "Links", "Rechts", or "Machine Stop")
    """
    # Convert sensor readings to tuple for easier pattern matching
    s = tuple(sensors)
    
    # Check for overshoot (all sensors on white)
    if s == (1, 1, 1, 1, 1):
        # Overshoot detected, use last significant decision if available
        for last_move in reversed(move_history):
            if last_move in ["Links", "Rechts"]:
                return last_move
        # If no turns in history, default to straight
        return "Rechtdoor"
    
    # Define direction patterns
    rechtdoor_patterns = [
        (1, 1, 0, 1, 1),  # Middle sensor on black
        (0, 0, 1, 0, 0),  # All outer sensors on black
        (0, 1, 1, 1, 0),  # Two outer sensors on black
        (0, 1, 1, 0, 0),  # Two outer right and center on black
        (0, 0, 1, 1, 0),  # Two outer left and center on black
        (0, 1, 0, 1, 1),  # Middle and outer left on black
        (1, 1, 0, 1, 0),  # Middle and outer right on black
        (1, 0, 0, 0, 1),  # Outer sensors on black
        (0, 1, 0, 0, 1),  # Outer right and inner left on black
        (1, 0, 1, 0, 0),  # Inner left and middle on black
        (0, 0, 1, 0, 1),  # Inner right and middle on black
    ]
    
    links_patterns = [
        (1, 0, 1, 1, 1),  # Left sensor on black
        (0, 1, 1, 1, 1),  # Left-most sensor on black
        (1, 0, 0, 1, 1),  # Middle and left sensor on black
        (0, 0, 0, 1, 1),  # Middle, left and left-most sensor on black
        (0, 0, 0, 0, 1),  # 4 left sensors on black
        (0, 0, 1, 1, 1),  # 2 left sensors on black
    ]
    
    rechts_patterns = [
        (1, 1, 1, 0, 1),  # Right sensor on black
        (1, 1, 1, 1, 0),  # Right-most sensor on black
        (1, 1, 0, 0, 1),  # Middle and right sensor on black
        (1, 1, 0, 0, 0),  # Middle, right and right-most sensor on black
        (1, 1, 1, 1, 1),  # All sensors on white
        (1, 0, 0, 0, 0),  # 4 right sensors on black
        (1, 1, 1, 0, 0),  # 2 right sensors on black
    ]
    
    # Special case for all black
    if s == (0, 0, 0, 0, 0):
        return "Rechtdoor"
    
    # Check patterns and return corresponding direction
    if s in rechtdoor_patterns:
        return "Rechtdoor"
    elif s in links_patterns:
        return "Links"
    elif s in rechts_patterns:
        return "Rechts"
    else:
        return "Machine Stop"

# Add a function to update the move history stack
def update_move_history(direction):
    global move_history
    # Only add to history if it's a significant direction
    if direction in ["Links", "Rechts", "Rechtdoor"]:
        move_history.append(direction)
        # Keep the history at a reasonable size
        if len(move_history) > MAX_HISTORY_SIZE:
            move_history.pop(0)


# Set up the IR sensors on A0 to A4 and register callbacks
sensors = {}
for i in range(0, 5):
    sensor_name = f'sensor_{i}'
    pin = board.get_pin(f'a:{i}:i')
    pin.register_callback(create_callback(sensor_name))
    pin.enable_reporting()
    sensors[sensor_name] = pin

# Main control loop
try:
    while True:
        # Check if it's time to update orders from database
        current_time = time.time()
        if current_time - last_db_update > DB_UPDATE_INTERVAL:
            open_orders = db.get_open_orders()
            last_db_update = current_time
        
        # Get sensor readings
        sensor_readings = [
            1 if sensor_values.get(f'sensor_{i}', 1) > 0.5 else 0
            for i in range(0, 5)
        ]
        
        # Determine direction and set motor speeds
        direction = determine_direction(sensor_readings)
        
        # Update move history with the current direction
        update_move_history(direction)
        
        # Print sensor values, direction, and open orders
        print(f"Sensor Values: {' '.join(map(str, sensor_readings))} - {direction}")
        if open_orders:
            print(f"Active Orders: {len(open_orders)} orders pending")
            # Print first order details as an example
            if len(open_orders) > 0:
                first_order = open_orders[0]
                print(f"Next Order: ID {first_order['id']} - {first_order['customer_name']}")
        
        # Set motor speeds based on direction
        if direction == "Rechtdoor":
            set_motor_speed(0.4, 0.4)
        elif direction == "Links":
            set_motor_speed(0, 0.4)
        elif direction == "Rechts":
            set_motor_speed(0.4, 0)
        elif direction == "Machine Stop":
            # Implement your logic for machine stop here
            set_motor_speed(0, 0)
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    # Clean up
    set_motor_speed(0, 0)
    board.exit()
    # Close database connection
    db.disconnect()


    