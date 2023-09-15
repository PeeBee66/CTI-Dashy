import os
import csv
import hashlib
from flask import Flask, session, render_template, redirect, url_for, request, Blueprint
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sub_apps import sub_app_blueprints
from config import Config
from sub_apps.api_search import api_search_bp

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = "login"

api_search_bp = Blueprint('api_search', __name__)

config_user_txt = "config/.user.txt"

if not os.path.exists(config_user_txt):
    with open(config_user_txt, "w") as f:
        f.write("admin,8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918,data_dupe,folder_size,hash_search,re_send,manifest,settings,user_mgmt,api_search\n")


class User(UserMixin):
    def __init__(self, username, hashed_password, allowed_apps):
        self.id = username
        self.hashed_password = hashed_password
        self.allowed_apps = allowed_apps

@login_manager.user_loader
def load_user(username):
    with open("config/.user.txt", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == username:
                hashed_password = row[1]
                allowed_apps = row[2:]
                return User(username, hashed_password, allowed_apps)
    return None

@api_search_bp.route('/api_search')
def api_search():
    print("Current User ID:", current_user.id)
    session['current_username'] = current_user.id  # Store the username in the session
    print("Stored in Session:", session['current_username'])
    return render_template('api_search.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = load_user(username)
        if user and check_password(password, user.hashed_password):
            login_user(user)
            print(f"User '{username}' logged in successfully.")
            return redirect(url_for("home"))
        else:
            print(f"Unsuccessful login attempt for user '{username}'.")  
            return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html", error=None)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Register sub-app blueprints when the app starts up
for sub_app in sub_app_blueprints:
    app.register_blueprint(sub_app)

@app.route('/')
def default_page():
    return render_template('index.html')

@app.route("/home")
@login_required
def home():
    return render_template("home.html", allowed_apps=current_user.allowed_apps)

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


def check_password(input_password, stored_hashed_password):
    hashed_input_password = hashlib.sha256(input_password.encode()).hexdigest()
    return hashed_input_password == stored_hashed_password

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
