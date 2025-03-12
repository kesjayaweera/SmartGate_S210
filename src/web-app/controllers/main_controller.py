from flask import Blueprint, jsonify

test_bp = Blueprint("test", "smartgate")

@test_bp.route('/test', methods=['GET'])
def get_status():
    return jsonify({"message": "Hello! Smart Gate Backend active!", "status": "Success!"})


