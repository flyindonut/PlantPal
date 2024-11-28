import os
import paho.mqtt.client as paho
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Dynamically generate a random secret key

# Hardcoded credentials
USERNAME = 'adr'
PASSWORD = 'pwd'

BROKER = "rpi2024.local"
PORT = 1883
TOPIC = "sensor/temperature"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)

sensor_data = {"temperature": [], "humidity": []}

def on_message(client, userdata, msg):
    data = msg.payload.decode().split(',')
    temperature, humidity = str(data[0]), str(data[1])
    sensor_data["temperature"].append(temperature)
    sensor_data["humidity"].append(humidity)

client = paho.Client()

client.on_connect = on_connect
client.on_message = on_message

if client.connect(BROKER, PORT, 60) != 0:
    print("Couldn't connect to the MQTT broker")
    exit(1)

client.loop_start()

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
    return jsonify(sensor_data)

@app.route('/activate')
def activate():
    return render_template('activate.html')

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
