# cycle_tracker/app.py
from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='webapp')

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('webapp', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)