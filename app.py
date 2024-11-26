import os
from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Dynamically generate a random secret key

# Hardcoded credentials
USERNAME = 'adr'
PASSWORD = 'pwd'

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

@app.route('/data')
@login_required
def data():
    return render_template('data.html')

@app.route('/statistics')
@login_required
def statistics():
    return render_template('statistics.html')

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

if __name__ == '__main__':
    app.run(debug=True)
