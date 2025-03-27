from flask import Blueprint, jsonify, render_template, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
import requests

oauth = OAuth()

home_bp = Blueprint("backend_homepage", "smartgate")
gates_bp = Blueprint("backend_gates", "smartgate")
about_bp = Blueprint("backend_about", "smartgate")
settings_bp = Blueprint("backend_setting", "smartgate")
status_bp = Blueprint("backend_status", "smartgate")
login_bp = Blueprint("backend_login", "smartgate")
callback_bp = Blueprint("backend_callback", "smartgate")
logout_bp = Blueprint("backend_logout", "smartgate")


def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(gates_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(callback_bp)
    app.register_blueprint(logout_bp)

    oauth.init_app(app)

    oauth.register(
        "github",
        client_id="Ov23liNZIYmArduFmbdg",
        client_secret="5562a74d01e9d3f61887e636ec6f05e184b267c6",
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        client_kwargs={"scope":"user"}
    )

@home_bp.route('/')
def home():
    user = session.get("user")
    return render_template('Index.html', user=user)

@gates_bp.route('/gates')
def gates():
    return render_template('gates.html')

@about_bp.route('/about')
def about():
    return render_template('About.html')

@settings_bp.route('/setting')
def setting():
    return render_template('setting.html')

@status_bp.route('/test', methods=['GET'])
def get_status():
    return jsonify(
        {
            "message": "Hello! Smart Gate Backend active!", 
            "status": "Success!"
        }
    )

@login_bp.route('/login')
def github_login():
    redirect_uri = url_for('backend_callback.github_callback_route', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@callback_bp.route('/callback')
def github_callback_route():
    token = oauth.github.authorize_access_token()
    # Get user details from GitHub API
    user_info = oauth.github.get("https://api.github.com/user").json()
    # Store user info in session
    session["user"] = {
        "username": user_info.get("login"),
        "id": user_info.get("id"),
        "avatar_url": user_info.get("avatar_url")
    }

    return redirect(url_for("backend_homepage.home"))

@logout_bp.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("github_token", None)
    return redirect(url_for("backend_homepage.home"))

