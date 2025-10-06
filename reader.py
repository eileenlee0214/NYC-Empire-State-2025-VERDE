import serial
import time
import csv
import requests
from datetime import datetime

# ----- CONFIG -----
SERIAL_PORT = '/dev/ttyACM0'   # e.g. COM3 on Windows, /dev/ttyACM0 or /dev/ttyUSB0 on Linux
BAUDRATE = 9600
CSV_FILE = 'ph_readings.csv'
API_URL = 'http://127.0.0.1:5000/api/data'  # Flask endpoint
API_KEY = 'CHANGE_ME_TO_A_SECRET_KEY'
# ------------------

def post_reading(timestamp_iso, ph_value):
    payload = {
        'timestamp': timestamp_iso,
        'ph': ph_value,
        'api_key': API_KEY
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        print("POST failed:", e)
        return False

def append_csv(timestamp_iso, ph_value):
    header = ['timestamp', 'ph']
    try:
        # create file and write header if not exists
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_iso, f"{ph_value:.3f}"])
    except Exception as e:
        print("CSV write failed:", e)

def main():
    # Open serial
    print("Opening serial port:", SERIAL_PORT)
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=10)
    time.sleep(2)  # allow Arduino reset
    print("Connected. Listening for lines...")

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            # Expecting lines like: pH,<millis>,<value>
            if line.startswith("pH,"):
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        millis_val = int(parts[1])
                        ph_val = float(parts[2])
                    except:
                        print("Malformed values", line)
                        continue

                    # timestamp on arrival (ISO 8601)
                    timestamp = datetime.utcnow().isoformat() + 'Z'
                    print(f"[{timestamp}] pH={ph_val:.3f} (millis:{millis_val})")

                    append_csv(timestamp, ph_val)

                    success = post_reading(timestamp, ph_val)
                    if success:
                        print("Posted to server")
                    else:
                        print("Failed to post (will still keep CSV)")

            else:
                # other debug lines
                print("RAW:", line)

        except KeyboardInterrupt:
            print("Stopping by user")
            break
        except Exception as e:
            print("Exception:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
