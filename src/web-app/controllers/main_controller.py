from flask import Blueprint, jsonify

test_bp = Blueprint("test", "smartgate")
data_bp = Blueprint("data", "smartgate")

@data_bp.route('/data', methods=['GET'])
def get_status():
    return jsonify({"message": "Hello! Smart Gate Backend active!", "status": "Success!"})

@test_bp.route('/')
def home():
    return "Hello from the test blueprint!"

