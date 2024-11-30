import os
import paho.mqtt.client as paho
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from collections import deque
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Dynamically generate a random secret key

# Hardcoded credentials
USERNAME = 'adr'
PASSWORD = 'pwd'

# MQTT Configuration
BROKER = "rpi2024.local"
PORT = 1883
TOPIC_TEMPERATURE = "plant/temperature"
TOPIC_HUMIDITY = "plant/humidity"
TOPIC_MOISTURE = "plant/moisture"
TOPIC_LED_CONTROL = "led/control"
TOPIC_VALVE_CONTROL = "plant/valve"

# Store live sensor data
sensor_data = {
    "temperature": deque(maxlen=15),
    "humidity": deque(maxlen=15),
    "moisture": None
}

# MQTT Client setup
mqtt_client = paho.Client()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe([
        (TOPIC_TEMPERATURE, 0),
        (TOPIC_HUMIDITY, 0),
        (TOPIC_MOISTURE, 0)
    ])

def on_message(client, userdata, msg):
    global sensor_data
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_TEMPERATURE:
        sensor_data["temperature"].append(float(payload))
    elif topic == TOPIC_HUMIDITY:
        sensor_data["humidity"].append(float(payload))
    elif topic == TOPIC_MOISTURE:
        sensor_data["moisture"] = "Dry" if int(payload) else "Moist"

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Start MQTT client in a background thread
def start_mqtt():
    if mqtt_client.connect(BROKER, PORT, 60) != 0:
        print("Couldn't connect to the MQTT broker")
        exit(1)
    mqtt_client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

# Login required decorator
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'logged_in' in session and session['logged_in']:
            return func(*args, **kwargs)
        else:
            flash("You must log in to access this page.", "warning")
            return redirect(url_for('login'))
    wrapper.__name__ = func.__name__  # To avoid Flask decorator issues
    return wrapper

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/historical')
def historicaldata_func():
    return render_template("historicaldata.html")

@app.route('/live-data-page')
def live_data_page():
    return render_template("live-data.html")

@app.route('/historical-data')
def historical_data():
    data = read_historical_data()
    return jsonify(data)

@app.route('/live-data')
def get_sensor_data():
    """
    API endpoint to provide live sensor data for temperature, humidity, and moisture.
    """
    return jsonify({
        "temperature": list(sensor_data["temperature"]),
        "humidity": list(sensor_data["humidity"]),
        "moisture": sensor_data["moisture"]
    })

@app.route('/activate')
def activate():
    return render_template('activate.html')

@app.route('/api/led-control', methods=['POST'])
def led_control():
    """
    API to control LEDs.
    """
    command = request.json.get('command')
    if command in ['on', 'off']:
        mqtt_client.publish(TOPIC_LED_CONTROL, command)
        return jsonify({'message': f'LEDs turned {command}.'}), 200
    return jsonify({'error': 'Invalid command'}), 400

@app.route('/api/valve-control', methods=['POST'])
def valve_control():
    """
    API to control the valve.
    """
    command = request.json.get('command')
    if command in ['open', 'close']:
        mqtt_client.publish(TOPIC_VALVE_CONTROL, command)
        return jsonify({'message': f'Valve {command}ed.'}), 200
    return jsonify({'error': 'Invalid command'}), 400

def read_historical_data():
    historical_data = []
    file_path = '../../Documents/PlantPal/static/historical_data.txt'

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                timestamp, value = line.strip().split(',')
                historical_data.append({'timestamp': timestamp, 'value': float(value)})
    return historical_data

if __name__ == '__main__':
    app.run(debug=True)
