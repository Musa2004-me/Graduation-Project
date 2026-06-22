import time
import json
import ssl
import threading
from flask import Flask, jsonify, request, render_template_string
import paho.mqtt.client as mqtt

# ==========================================
# ⚙️ CLOUD DASHBOARD CONFIGURATION
# ==========================================
CART_ID = "cart_001"
AWS_IOT_ENDPOINT = "ajelyhc78s5bv-ats.iot.eu-central-1.amazonaws.com"
PORT = 8883

# X.509 Certificate Paths (referencing the certs folder in the car directory)
CA_CERT = "../car/certs/cart_001/root.pem"
DEVICE_CERT = "../car/certs/cart_001/certificate.pem.crt"
PRIVATE_KEY = "../car/certs/cart_001/private.pem.key"

# MQTT Topics
TELEMETRY_TOPIC = f"carta/telemetry/{CART_ID}"
COMMANDS_TOPIC = f"carta/commands/{CART_ID}"

# In-memory database to store latest telemetry logs
latest_telemetry = {
    "cart_id": CART_ID,
    "battery_percentage": 100,
    "latitude": 30.044420,
    "longitude": 31.235712,
    "timestamp": "N/A",
    "status": "Offline"
}

# Thread Lock for shared telemetry
telemetry_lock = threading.Lock()

# Initialize Flask app
app = Flask(__name__)

# ==========================================
# 📡 CLOUD MQTT CLIENT DEFINITION
# ==========================================
cloud_mqtt = mqtt.Client(client_id="carta_cloud_dashboard")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("☁️ [AWS CLOUD DASHBOARD] Connected to AWS IoT Core securely!")
        client.subscribe(TELEMETRY_TOPIC, qos=1)
        print(f"☁️ Subscribed to Telemetry Topic: {TELEMETRY_TOPIC}")
    else:
        print(f"❌ Cloud MQTT Connection failed with code {rc}")

def on_message(client, userdata, msg):
    global latest_telemetry
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"📥 [TELEMETRY INGESTED FROM AWS] {payload}")
        with telemetry_lock:
            latest_telemetry.update({
                "battery_percentage": payload.get("battery_percentage", 100),
                "latitude": payload.get("latitude", 30.044420),
                "longitude": payload.get("longitude", 31.235712),
                "timestamp": payload.get("timestamp", "N/A"),
                "status": "Online"
            })
    except Exception as e:
        print(f"❌ Error decoding incoming telemetry: {e}")

# Configure SSL and attach callbacks for the dashboard client
cloud_mqtt.tls_set(ca_certs=CA_CERT, 
                   certfile=DEVICE_CERT, 
                   keyfile=PRIVATE_KEY, 
                   cert_reqs=ssl.CERT_REQUIRED, 
                   tls_version=ssl.PROTOCOL_TLSv1_2, 
                   ciphers=None)
cloud_mqtt.on_connect = on_connect
cloud_mqtt.on_message = on_message

# ==========================================
# 🌐 WEB DASHBOARD INTERFACE
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carta 001 - Cloud Command Center</title>
    
    <!-- Google Fonts & Leaflet Mapping -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <style>
        :root {
            --bg-dark: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.6);
            --border-glow: rgba(0, 168, 204, 0.2);
            --primary-cyan: #00e5ff;
            --accent-green: #39ff14;
            --alert-red: #ff3838;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Ambient Background Glows */
        .ambient-glow-1 {
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(0, 229, 255, 0.08) 0%, rgba(0, 0, 0, 0) 70%);
            top: -100px;
            left: -100px;
            z-index: 0;
        }

        .ambient-glow-2 {
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(57, 255, 20, 0.05) 0%, rgba(0, 0, 0, 0) 70%);
            bottom: -100px;
            right: -100px;
            z-index: 0;
        }

        /* Header bar */
        header {
            width: 100%;
            padding: 20px 40px;
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-ring {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid var(--primary-cyan);
            border-top-color: transparent;
            animation: spin 1.5s linear infinite;
        }

        header h1 {
            font-weight: 800;
            font-size: 24px;
            letter-spacing: 1px;
            background: linear-gradient(90deg, var(--primary-cyan), #ab47bc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .connection-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px 16px;
            border-radius: 50px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 14px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--text-muted);
            box-shadow: 0 0 10px var(--text-muted);
        }

        .status-dot.online {
            background-color: var(--accent-green);
            box-shadow: 0 0 12px var(--accent-green);
        }

        /* Layout Grid */
        main {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 450px;
            padding: 30px;
            gap: 30px;
            z-index: 10;
        }

        @media (max-width: 1024px) {
            main {
                grid-template-columns: 1fr;
            }
        }

        /* Left Side - Interactive Map */
        .map-container {
            position: relative;
            background: var(--card-bg);
            border-radius: 20px;
            border: 1px solid var(--border-glow);
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.4);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            min-height: 500px;
        }

        #map {
            flex: 1;
            width: 100%;
        }

        .card-header {
            padding: 20px 25px;
            background: rgba(22, 28, 45, 0.9);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-header h2 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-main);
        }

        /* Right Side - Control Panel */
        .control-panel {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--border-glow);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(12px);
        }

        /* Telemetry Readouts */
        .telemetry-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }

        .readout {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .readout-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .readout-value {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-main);
        }

        /* Battery Visualization */
        .battery-ring-container {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-top: 20px;
        }

        .battery-gauge {
            position: relative;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .battery-number {
            font-size: 18px;
            font-weight: 800;
            color: var(--text-main);
        }

        .battery-meta {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        /* Action Buttons */
        .buttons-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 20px;
        }

        .action-btn {
            position: relative;
            width: 100%;
            padding: 16px;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            font-weight: 700;
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .btn-unlock {
            background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(0, 180, 219, 0.3);
        }

        .btn-unlock:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 180, 219, 0.5);
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        }

        .btn-stop {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 65, 108, 0.3);
        }

        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 65, 108, 0.5);
            background: linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%);
        }

        .action-btn:active {
            transform: translateY(1px);
        }

        /* Terminal Activity Logger */
        .terminal-container {
            background: rgba(5, 7, 12, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 15px;
            height: 150px;
            font-family: monospace;
            font-size: 13px;
            overflow-y: auto;
            color: #a8ffb2;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .terminal-line {
            line-height: 1.4;
        }

        .terminal-time {
            color: var(--text-muted);
            margin-right: 8px;
        }

        .terminal-info {
            color: var(--primary-cyan);
        }

        .terminal-success {
            color: var(--accent-green);
        }

        .terminal-error {
            color: var(--alert-red);
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>

    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>

    <header>
        <div class="logo-group">
            <div class="logo-ring"></div>
            <h1>CARTA Command Center</h1>
        </div>
        <div class="connection-badge">
            <div id="conn-dot" class="status-dot"></div>
            <span id="conn-text">Checking connection...</span>
        </div>
    </header>

    <main>
        <!-- Map Panel -->
        <section class="map-container">
            <div class="card-header">
                <h2>Real-Time GPS Location Tracking</h2>
                <div style="font-size: 13px; color: var(--text-muted);" id="last-updated">Last Updated: N/A</div>
            </div>
            <div id="map"></div>
        </section>

        <!-- Right Side controls -->
        <section class="control-panel">
            
            <!-- Real-time Telemetry values -->
            <div class="glass-card">
                <h2>Physical Cart Telemetry</h2>
                
                <div class="battery-ring-container">
                    <div class="battery-gauge">
                        <!-- Simple circular visual -->
                        <svg width="80" height="80" viewBox="0 0 80 80">
                            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="6"/>
                            <circle id="battery-progress" cx="40" cy="40" r="34" fill="none" 
                                    stroke="var(--accent-green)" stroke-dasharray="213.6" stroke-dashoffset="0"
                                    stroke-linecap="round" stroke-width="6" transform="rotate(-90 40 40)"/>
                        </svg>
                        <div style="position: absolute;" class="battery-number" id="battery-percentage">--%</div>
                    </div>
                    <div class="battery-meta">
                        <span style="font-weight: 600; font-size: 16px;">Power System Status</span>
                        <span style="font-size: 12px; color: var(--text-muted);" id="battery-status-text">Ingesting battery cycles...</span>
                    </div>
                </div>

                <div class="telemetry-grid">
                    <div class="readout">
                        <span class="readout-label">Latitude</span>
                        <span class="readout-value" id="lat-val">--.------</span>
                    </div>
                    <div class="readout">
                        <span class="readout-label">Longitude</span>
                        <span class="readout-value" id="lon-val">--.------</span>
                    </div>
                    <div class="readout" style="grid-column: span 2;">
                        <span class="readout-label">Cart ID Identification</span>
                        <span class="readout-value" style="font-size: 15px; color: var(--primary-cyan);">cart_001 (Germany Region)</span>
                    </div>
                </div>
            </div>

            <!-- AWS Cloud Commands -->
            <div class="glass-card">
                <h2>AWS Tele-Operation Commands</h2>
                <p style="font-size: 13px; color: var(--text-muted); margin-top: 5px;">
                    Execute control events instantly via the secure AWS IoT Core MQTT broker.
                </p>

                <div class="buttons-container">
                    <button class="action-btn btn-unlock" onclick="sendCommand('unlock_doors')">
                        🔓 Unlock Solenoid
                    </button>
                    <button class="action-btn btn-stop" onclick="sendCommand('emergency_stop')">
                        🚨 EMERGENCY STOP
                    </button>
                </div>
            </div>

            <!-- Event Logs terminal -->
            <div class="glass-card" style="flex: 1; display: flex; flex-direction: column;">
                <h2>AWS Live Event Logger</h2>
                <div class="terminal-container" id="terminal" style="margin-top: 15px; flex: 1;">
                    <div class="terminal-line">
                        <span class="terminal-time">[System]</span> Initializing Cloud Dashboard secure socket connection...
                    </div>
                </div>
            </div>

        </section>
    </main>

    <script>
        // Leaflet Map Initialization
        // Start centered on Cairo (simulation coordinates default)
        const map = L.map('map').setView([30.044420, 31.235712], 17);
        
        // Add modern custom dark maps or openstreet maps tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
        }).addTo(map);

        // Add custom pulsing marker for the cart
        const cartIcon = L.divIcon({
            className: 'custom-pulsing-icon',
            html: '<div style="width:16px; height:16px; background:#00e5ff; border:3px solid #fff; border-radius:50%; box-shadow:0 0 10px #00e5ff;"></div>',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });

        const marker = L.marker([30.044420, 31.235712], {icon: cartIcon}).addTo(map);
        marker.bindPopup("<b>Cart 001</b><br>Secured Edge Connectivity active.").openPopup();

        // Logger Functionality
        function log(message, type = 'info') {
            const term = document.getElementById('terminal');
            const timeStr = new Date().toLocaleTimeString();
            let typeClass = 'terminal-info';
            if (type === 'success') typeClass = 'terminal-success';
            if (type === 'error') typeClass = 'terminal-error';
            
            term.innerHTML += `
                <div class="terminal-line">
                    <span class="terminal-time">[${timeStr}]</span>
                    <span class="${typeClass}">${message}</span>
                </div>
            `;
            term.scrollTop = term.scrollHeight; // Auto-scroll to bottom
        }

        // Fetch updates from Flask Local API
        function pollTelemetry() {
            fetch('/api/telemetry')
                .then(res => res.json())
                .then(data => {
                    if (data.status === "Online") {
                        // Update Connection Badge
                        document.getElementById('conn-dot').className = 'status-dot online';
                        document.getElementById('conn-text').innerText = 'Connected Live (AWS Central)';
                        
                        // Update Telemetry Data in UI
                        document.getElementById('lat-val').innerText = data.latitude.toFixed(6);
                        document.getElementById('lon-val').innerText = data.longitude.toFixed(6);
                        document.getElementById('battery-percentage').innerText = data.battery_percentage + '%';
                        document.getElementById('last-updated').innerText = 'Last Updated: ' + data.timestamp;

                        // Battery visual
                        const progress = document.getElementById('battery-progress');
                        const pct = data.battery_percentage;
                        const offset = 213.6 - (213.6 * pct / 100);
                        progress.style.strokeDashoffset = offset;

                        // Battery status color & label
                        if (pct > 50) {
                            progress.style.stroke = "var(--accent-green)";
                            document.getElementById('battery-status-text').innerText = "Voltage Stable. Capacity Healthy.";
                        } else if (pct > 20) {
                            progress.style.stroke = "orange";
                            document.getElementById('battery-status-text').innerText = "Warning: Charge dropping. Monitor.";
                        } else {
                            progress.style.stroke = "var(--alert-red)";
                            document.getElementById('battery-status-text').innerText = "CRITICAL: Solenoid threshold near. Charge BMS.";
                        }

                        // Relocate Map View Marker
                        const newLatLng = new L.LatLng(data.latitude, data.longitude);
                        marker.setLatLng(newLatLng);
                        // Optional: Pan map to follow the cart
                        map.panTo(newLatLng);
                    } else {
                        document.getElementById('conn-dot').className = 'status-dot';
                        document.getElementById('conn-text').innerText = 'Awaiting Cart Signal (Offline)';
                    }
                })
                .catch(err => {
                    console.error("Telemetry poll failed:", err);
                });
        }

        // Send Command to local Flask server which publishes via MQTT
        function sendCommand(action) {
            log(`Publishing command: '${action}' to AWS Core...`, 'info');
            
            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: action })
            })
            .then(res => res.json())
            .then(data => {
                if (data.message) {
                    log(`AWS MQTT Confirm: ${data.message}`, 'success');
                } else {
                    log(`AWS MQTT Refused: ${data.error}`, 'error');
                }
            })
            .catch(err => {
                log(`Network error sending command: ${err}`, 'error');
            });
        }

        // Connect! Start polling every 1.5 seconds
        setInterval(pollTelemetry, 1500);
        log("Listening on AWS Gateway for live Cart 001 publishes...", 'success');
    </script>
</body>
</html>
"""

# ==========================================
# 🔌 FLASK ENDPOINTS
# ==========================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    with telemetry_lock:
        return jsonify(latest_telemetry)

@app.route('/api/command', methods=['POST'])
def post_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "Missing parameter 'command'"}), 400
        
    command = data['command']
    allowed_commands = ["unlock_doors", "emergency_stop"]
    
    if command not in allowed_commands:
        return jsonify({"error": f"Invalid command: '{command}'"}), 400

    # Publish MQTT payload over the AWS Cloud connection
    payload = {"command": command}
    try:
        # Publish command to AWS IoT commands topic
        cloud_mqtt.publish(COMMANDS_TOPIC, json.dumps(payload), qos=1)
        print(f"☁️ [AWS DASHBOARD PUBLISHED] {command} onto {COMMANDS_TOPIC}")
        return jsonify({"message": f"Published '{command}' securely to AWS IoT Core!"}), 200
    except Exception as e:
        return jsonify({"error": f"MQTT Publish failed: {str(e)}"}), 500

# ==========================================
# 🏁 DASHBOARD RUNNER
# ==========================================
if __name__ == '__main__':
    print("⏳ Initializing AWS IoT Core loop inside cloud dashboard...")
    try:
        # Connect to AWS IoT Core as the central dashboard hub
        cloud_mqtt.connect(AWS_IOT_ENDPOINT, PORT, keepalive=60)
        cloud_mqtt.loop_start()
    except Exception as e:
        print(f"⚠️ Could not connect Dashboard directly to AWS IoT Core: {e}")
        print("👉 The dashboard will run, but live AWS MQTT features require correct certs path.")

    # Start Flask Webserver
    print("🚀 Booting Cloud Dashboard on http://127.0.0.1:5000/")
    app.run(host='127.0.0.1', port=5000, debug=False)
