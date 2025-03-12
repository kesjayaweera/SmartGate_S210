from flask import Blueprint, jsonify

data_bp = Blueprint("data", "smartgate")

@data_bp.route('/data', methods=['GET'])
def get_status():
    return jsonify({"message": "Hello! Smart Gate Backend active!", "status": "Success!"})


