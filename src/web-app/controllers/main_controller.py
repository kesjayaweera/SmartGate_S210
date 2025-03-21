from flask import Blueprint, jsonify, render_template, url_for, session, redirect
from authlib.integrations.flask_client import OAuth

# oauth = OAuth()

backend_test_bp = Blueprint("testpage", "smartgate")
test_bp = Blueprint("test", "smartgate")

def register_blueprints(app):
    app.register_blueprint(backend_test_bp)
    app.register_blueprint(test_bp)

@backend_test_bp.route('/')
def backend_test_page():
    return render_template('test.html')

@test_bp.route('/test', methods=['GET'])
def get_status():
    return jsonify(
        {
            "message": "Hello! Smart Gate Backend active!", 
            "status": "Success!"
        }
    )

