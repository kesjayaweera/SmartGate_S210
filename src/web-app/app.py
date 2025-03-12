from flask import Flask
from controllers.main_controller import test_bp

app = Flask("smartgate")

app.register_blueprint(test_bp)

if __name__ == "__main__":
    app.run(debug=True)
