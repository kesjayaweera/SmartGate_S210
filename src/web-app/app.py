from flask import Flask
from controllers.main_controller import data_bp

app = Flask("smartgate")

app.register_blueprint(data_bp)

if __name__ == "__main__":
    app.run(debug=True)
