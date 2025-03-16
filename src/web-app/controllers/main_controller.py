from flask import Blueprint, jsonify, render_template

backend_test_bp = Blueprint("testpage", "smartgate")
test_bp = Blueprint("test", "smartgate")

@backend_test_bp.route('/')
def backend_test_page():
    return render_template('test.html')

@test_bp.route('/test', methods=['GET'])
def get_status():
    return jsonify({"message": "Hello! Smart Gate Backend active!", "status": "Success!"})

