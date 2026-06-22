import time
import json
import ssl
import threading
import os
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import paho.mqtt.client as mqtt

# --- ROS2 IMPORTS ---
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String, Bool
    ROS2_SUPPORTED = True
except ImportError:
    print("⚠️ ROS2 (rclpy) environment not found. ROS2 publishing will be simulated.")
    ROS2_SUPPORTED = False

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
CART_ID = "cart_001"
AWS_IOT_ENDPOINT = "ajelyhc78s5bv-ats.iot.eu-central-1.amazonaws.com" 
PORT = 8883

CA_CERT = "./certs/cart_001/root.pem"
DEVICE_CERT = "./certs/cart_001/certificate.pem.crt"
PRIVATE_KEY = "./certs/cart_001/private.pem.key"

TELEMETRY_TOPIC = "carts/cart_001/telemetry"
COMMANDS_TOPIC = "carts/cart_001/command"

# ==========================================
# 🗺️ GLOBAL THREAD-SAFE STATE
# ==========================================
gps_lock = threading.Lock()
gps_latitude = 30.044420
gps_longitude = 31.235712
current_status = "idle"

# ROS2 Global Publisher Reference
ros_cmd_pub = None
ros_lock_pub = None

# ==========================================
# 🤖 ROS2 NODE DEFINITION
# ==========================================
class CartaBridgeNode(Node):
    def __init__(self):
        super().__init__('carta_aws_bridge')
        global ros_cmd_pub, ros_lock_pub
        
        # Topic 1: Vehicle State Commands (/cart/command_state)
        ros_cmd_pub = self.create_publisher(String, '/cart/command_state', 10)
        # Topic 2: Explicit Door Lock/Unlock (/cart/door_lock)
        ros_lock_pub = self.create_publisher(Bool, '/cart/door_lock', 10)
        
        self.get_logger().info('✅ ROS2 Bridge Node initialized successfully.')

def ros2_spin_thread():
    if ROS2_SUPPORTED:
        rclpy.init()
        node = CartaBridgeNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    else:
        print("💻 [SIMULATED] ROS2 spin executor loop active background.")

# ==========================================
# 📱 MOBILE PHONE HTTP SERVER RECEIVER
# ==========================================
class MobileGPSRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global gps_latitude, gps_longitude
        try:
            # Read the incoming payload body
            content_length_header = self.headers.get('Content-Length')
            content_length = int(content_length_header) if content_length_header else 0
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
            
            lat = None
            lon = None

            if post_data:
                try:
                    json_data = json.loads(post_data)
                    
                    # 1. Handle Transistor Background-Geolocation Array (Batch Sync)
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0] # Grab the first location event in the batch
                        
                    # 2. Extract from Transistor's nested format: location -> coords -> latitude
                    if 'location' in json_data and 'coords' in json_data['location']:
                        lat = json_data['location']['coords']['latitude']
                        lon = json_data['location']['coords']['longitude']
                        
                    # 3. Fallback for basic flat JSON format
                    elif 'lat' in json_data and 'lon' in json_data:
                        lat = json_data['lat']
                        lon = json_data['lon']
                        
                except json.JSONDecodeError:
                    pass
            
            # 4. Fallback for URL parameter format (if JSON decode failed or no body)
            if lat is None or lon is None:
                parsed_path = urllib.parse.urlparse(self.path)
                url_params = urllib.parse.parse_qs(parsed_path.query)
                if 'lat' in url_params and 'lon' in url_params:
                    lat = url_params['lat'][0]
                    lon = url_params['lon'][0]

            # 5. Update the global variables if we successfully found the coordinates
            if lat is not None and lon is not None:
                with gps_lock:
                    gps_latitude = float(lat)
                    gps_longitude = float(lon)
                print(f"🎯 [GPS UPDATE] Live coordinates: Lat {gps_latitude}, Lon {gps_longitude}")
            else:
                # Print the raw data so you can see exactly what the phone is sending if it fails
                print(f"⚠️ [WARNING] Ping received, but couldn't find coordinates. Raw payload:\n{post_data[:300]}")

        except Exception as e:
            print(f"❌ Mobile parse error: {e}")
            
        self.send_response(200)
        self.end_headers()

def mobile_server_thread():
    server_address = ('0.0.0.0', 5555)
    httpd = HTTPServer(server_address, MobileGPSRequestHandler)
    print("[*] Mobile Phone HTTP Sync engine listening on port 5555...")
    httpd.serve_forever()

# ==========================================
# 📡 MQTT CALLBACKS & ROS2 TRANSLATION
# ==========================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to AWS IoT Core securely!")
        client.subscribe(COMMANDS_TOPIC, qos=1)
    else:
        print(f"❌ Connection failed with error code {rc}")

def on_message(client, userdata, msg):
    global current_status, ros_cmd_pub, ros_lock_pub
    print(f"\n📥 [CLOUD COMMAND RECEIVED]")
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(json.dumps(payload, indent=2))
        
        # Extract command properties
        cmd_value = payload.get("command", "").lower()
        status_value = payload.get("status", "").lower()

        # --- 💥 TRANSLATE & PUBLISH TO ROS2 TOPICS 💥 ---
        
        # 1. State/Emergency management 
        if status_value or cmd_value:
            state_msg = String()
            state_msg.data = status_value if status_value else cmd_value
            
            if ros_cmd_pub:
                ros_cmd_pub.publish(state_msg)
                print(f"🤖 [ROS2 PUBLISH] Sent state '{state_msg.data}' to topic /cart/command_state")
            
            if status_value:
                current_status = status_value

        # 2. Lock/Unlock direct handling
        if "unlock" in cmd_value or "unlock" in status_value:
            lock_msg = Bool()
            lock_msg.data = False  # False = Unlocked state
            if ros_lock_pub:
                ros_lock_pub.publish(lock_msg)
                print("🤖 [ROS2 PUBLISH] Sent 'False' (Unlock) to topic /cart/door_lock")

    except Exception as e:
        print(f"❌ Error compiling or publishing ROS2 message structure: {e}")

# ==========================================
# 🚀 TELEMETRY PUBLISHER
# ==========================================
def telemetry_loop(client):
    while True:
        with gps_lock:
            lat = gps_latitude
            lon = gps_longitude

        payload = {
            "cart_id": CART_ID,
            "timestamp": int(time.time()),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "battery": 95,
            "battery_level": 95,
            "status": current_status
        }
        
        client.publish(TELEMETRY_TOPIC, json.dumps(payload), qos=1)
        print(f"📤 [TELEMETRY SENT TO AWS]: Lat: {payload['lat']}, Lon: {payload['lon']} | Status: {payload['status']}")
        time.sleep(5)

# ==========================================
# 🏁 MAIN EXECUTION
# ==========================================
if __name__ == '__main__':
    # Initialize background threads
    threading.Thread(target=ros2_spin_thread, daemon=True).start()
    threading.Thread(target=mobile_server_thread, daemon=True).start()

    # Configure MQTT Connection
    client = mqtt.Client(client_id=CART_ID)
    client.tls_set(ca_certs=CA_CERT, certfile=DEVICE_CERT, keyfile=PRIVATE_KEY, 
                   cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.on_connect = on_connect
    client.on_message = on_message

    print("⏳ Connecting to AWS IoT Core Interface...")
    try:
        client.connect(AWS_IOT_ENDPOINT, PORT, keepalive=60)
    except Exception as e:
        print(f"❌ MQTT Connection error: {e}")
        exit(1)

    client.loop_start()

    try:
        telemetry_loop(client)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down bridge...")
        client.loop_stop()
        client.disconnect()
