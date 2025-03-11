from flask import Flask
from controllers.main_controller import test_bp, data_bp

app = Flask("smartgate")

# Register the Blueprint
# test_bp will not be used anymore
# app.register_blueprint(test_bp)
app.register_blueprint(data_bp)

if __name__ == "__main__":
    app.run(debug=True)
