# Cart 001: Hardware Interfacing & Cloud Command Center

This project outlines a high-fidelity, multithreaded mechatronic interfacing system developed for the **Cart 001** edge platform. The script handles high-performance, non-blocking telemetry acquisition alongside reactive remote AWS Cloud command execution.

---

## 🏗️ System Architecture & Data Flow

Below is the mechatronic block diagram illustrating how the Raspberry Pi coordinates parallel tasks, translates physical events, and interfaces securely with the AWS IoT Core endpoint.

```mermaid
graph TD
    %% Hardware Inputs
    GPS[NEO-M8N GPS Module] -- "NMEA Sentences (UART)" --> Serial0[/dev/ttyUSB0 or /dev/serial0]
    BMS[Smart BMS / Fuel Gauge] -- "UART / I2C" --> Serial1[I2C Bus 1 or /dev/ttyUSB1]
    
    %% Software Threads
    subgraph Raspberry Pi 4 [Cart Edge Software]
        GPSThread[Background GPS Thread] -- "Decodes NMEA (GNGGA/GPGGA)" --> ThreadSafeGPS[(Thread-Safe GPS State)]
        BMSFunc[BMS Reader] -- "Laptop / I2C / UART Daly" --> GetTelemetry[get_gps_and_battery]
        ThreadSafeGPS --> GetTelemetry
        
        TelemetryLoop[Telemetry Loop - 5s] -- "JSON Packets" --> MQTTClient[Paho MQTT Client]
        
        MQTTClient -- "Subscribed: commands" --> Callback[on_message Callback]
        Callback -- "Unlocks Solenoid" --> GPIO18[GPIO Pin 18 - Relay]
        Callback -- "Emergency Cutoff" --> GPIO23[GPIO Pin 23 - Kill Switch]
    end

    %% Cloud backend
    MQTTClient -- "Publish: telemetry" --> AWS[AWS IoT Core Frankfurt]
    AWS -- "Push: commands" --> MQTTClient
```

---

## 📡 1. Non-Blocking GPS Interfacing (Telemetry Up)

Rather than using blocking `serial.readline()` calls inside the 5-second telemetry loop (which would cause network lag and delay MQTT packet handshakes), we use a dedicated **daemon thread** to receive GPS telemetry.

### Features
* **Multi-Port Auto-Scan**: Scans `/dev/ttyUSB0` (USB GPS), `/dev/serial0` (Raspberry Pi default UART), and `/dev/ttyAMA0` in priority order.
* **Auto-Reconnection**: Automatically detects disconnections or serial drops and handles re-handshaking without crashing the application.
* **Robust NMEA Parser**: Parses `$GNGGA` and `$GPGGA` sentences and converts raw DDMM.MMMM coordinates to standard Decimal Degrees.
* **Visual Cairo Drift Simulator**: When testing on a laptop or inside a workshop without direct satellite visibility, the system drifts coordinates near Cairo coordinates to keep cloud dashboard map widgets visually dynamic.

---

## 🔋 2. Multi-Source Battery Monitoring (BMS)

To support multiple deployment stages, the system automatically detects and reads battery percentage from four different sources:

| Source Priority | Interface / Device | Implementation Logic | Use Case |
| :--- | :--- | :--- | :--- |
| **1. Developer Simulation** | Laptop `/sys/class/power_supply/` | Reads BAT1 capacity directly from Linux system files. | Desktop/Laptop testing. |
| **2. Physical I2C Fuel Gauge** | MAX17043 (Address: `0x36`) | Queries standard battery fuel gauge registers over I2C. | Low-power portable rigs. |
| **3. Physical UART BMS** | Daly UART Smart BMS (`/dev/ttyUSB1`) | Issues a UART binary request and parses the returning packet. | Large physical e-carts. |
| **4. Simulated Battery Drain** | Thread-Safe Memory | Slowly drains charge from 95% down to 15% and resets. | Full hardware fallback simulation. |

---

## 🔌 3. Configurable Relay Logic (Commands Down)

Depending on the physical relays or optocouplers used, your circuitry might be **active-high** (triggering on a high state) or **active-low** (triggering on a low state). We've exposed highly explicit toggle flags at the top of the file to configure this without rewriting the callback functions:

```python
LOCK_ACTIVE_HIGH = True  # True: HIGH to unlock solenoid, LOW to lock. False: LOW to unlock, HIGH to lock.
MOTOR_KILL_ACTIVE_HIGH = True # True: LOW cuts motor power, HIGH runs. False: HIGH cuts power, LOW runs.
```

### Action Mapping Table

| Command Received | Logical Action | Pin Number (BCM) | Physical Output Level (Active-High) | Physical Output Level (Active-Low) |
| :--- | :--- | :--- | :--- | :--- |
| **`unlock_doors`** | **Unlock** (5s) then **Relock** | Pin 18 (Solenoid) | `HIGH` (Unlock) $\rightarrow$ `LOW` (Lock) | `LOW` (Unlock) $\rightarrow$ `HIGH` (Lock) |
| **`emergency_stop`** | **Cut Power** (Permanent lock) | Pin 23 (Kill Switch) | `LOW` (Cut) | `HIGH` (Cut) |

---

## 🚀 How to Run and Test

### 1. Verification on Development Laptop
You can test the connectivity immediately on your laptop in simulation mode. Since `RPi.GPIO` is missing on your computer, the system runs in **Cloud-Simulation Mode** and handles mock pins gracefully.

Run the script from the workspace directory:
1. **Initialize the Web Dashboard**:
   ```bash
   make run-cloud
   ```
2. **Initialize the Cart Edge Node**:
   ```bash
   make run-car
   ```
3. **Open browser**: Go to **`http://127.0.0.1:5000/`** to view telemetry map plotting and execute override locks!

### 2. Deploying on Physical Raspberry Pi
Once you move the script to your Raspberry Pi:

1. **Install Serial Dependencies**:
   ```bash
   make setup
   ```
2. **Grant Serial Port Permissions**:
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   *(Note: Remember to log out and log back in for changes to take effect!)*
3. **Execute edge software**:
   ```bash
   make run-car
   ```
