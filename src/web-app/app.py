from flask import Flask
from controllers.main_controller import test_bp, backend_test_bp

app = Flask("smartgate")

app.register_blueprint(backend_test_bp)
app.register_blueprint(test_bp)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
