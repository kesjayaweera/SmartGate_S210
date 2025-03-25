from flask import Flask
from controllers.main_controller import register_blueprints

def create_sg_app():
    app = Flask("smartgate")
    app.secret_key = "a0f6c9b71df3b8fb756c91f2794b501c5e560fbfb93767c904f9354926554cd0"

    register_blueprints(app)

    return app

if __name__ == "__main__":
    app = create_sg_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
