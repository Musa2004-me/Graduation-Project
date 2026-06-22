import json
import time
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# --- CONFIGURATION ---
CLIENT_ID = "cart_001"
ENDPOINT = "ajelyhc78s5bv-ats.iot.eu-central-1.amazonaws.com"
PORT = 8883
PUB_TOPIC = "carts/cart_001/telemetry"
SUB_TOPIC = "carts/cart_001/command"

PATH_TO_ROOT_CA = "root.pem"
PATH_TO_CERT = "certificate.pem.crt"
PATH_TO_KEY = "private.pem.key"

LOCAL_PORT = 5555 

# --- GLOBAL STATE ---
latest_gps = {"lat": 30.044420, "lon": 31.235712}  # Fallback defaults
current_status = "idle"
battery_mock = 95  

# --- LOCAL GPS RECEIVER SERVER ---
# --- LOCAL GPS RECEIVER SERVER ---
class GPSRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global latest_gps
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # This parses parameters whether they come in via the path or raw body
            params = urllib.parse.parse_qs(post_data)
            
            # Backup check: if the app sent it as JSON instead of URL-encoded parameters
            if not params:
                try:
                    json_data = json.loads(post_data)
                    if 'lat' in json_data and 'lon' in json_data:
                        latest_gps["lat"] = float(json_data['lat'])
                        latest_gps["lon"] = float(json_data['lon'])
                except:
                    pass
            else:
                if 'lat' in params and 'lon' in params:
                    latest_gps["lat"] = float(params['lat'][0])
                    latest_gps["lon"] = float(params['lon'][0])
        except Exception as e:
            print(f"Parsing error: {e}")
            
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return # Suppress log spam
def http_gps_listener():
    server_address = ('0.0.0.0', LOCAL_PORT)
    httpd = HTTPServer(server_address, GPSRequestHandler)
    print(f"[*] Local Ubuntu server listening for mobile updates on port {LOCAL_PORT}...")
    httpd.serve_forever()

# --- MQTT CALLBACKS ---
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    global current_status
    print(f"\n[!] Command received from AWS cloud on topic {topic}")
    try:
        data = json.loads(payload.decode("utf-8"))
        print(json.dumps(data, indent=2))
        if "status" in data:
            current_status = data["status"]
    except Exception as e:
        print(f"Error parsing command payload: {e}")

# --- MAIN METHOD ---
def main():
    print("[*] Launching connection to AWS IoT Core...")
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT, port=PORT,
        cert_filepath=PATH_TO_CERT, pri_key_filepath=PATH_TO_KEY, ca_filepath=PATH_TO_ROOT_CA,
        client_id=CLIENT_ID, clean_session=False, keep_alive_secs=30
    )

    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("[+] Connected securely to AWS Broker!")

    mqtt_connection.subscribe(topic=SUB_TOPIC, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received)

    # Fire up the phone listening thread
    threading.Thread(target=http_gps_listener, daemon=True).start()

    try:
        while True:
            payload = {
                "cart_id": CLIENT_ID,
                "timestamp": int(time.time()),
                "lat": latest_gps["lat"],
                "lon": latest_gps["lon"],
                "battery": battery_mock,
                "battery_level": battery_mock,
                "status": current_status
            }
            
            mqtt_connection.publish(topic=PUB_TOPIC, payload=json.dumps(payload), qos=mqtt.QoS.AT_LEAST_ONCE)
            print(f"[Sent to AWS]: Lat: {payload['lat']}, Lon: {payload['lon']} | Status: {payload['status']}")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n[-] Shutting down...")
        mqtt_connection.disconnect().result()

if __name__ == "__main__":
    main()
