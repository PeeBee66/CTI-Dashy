# project_root/app/main.py
from flask import render_template
from app import app

@app.route('/')
def index():
    return render_template('index.html', active_tab='doogle')