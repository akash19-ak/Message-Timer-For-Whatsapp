import os
import logging
from flask import Flask
from flask_cors import CORS
from models import db
from routes import api
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def create_app():
    app = Flask(__name__)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'birthday.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)

    with app.app_context():
        db.create_all()
        logging.info("Database tables created / verified.")

    app.register_blueprint(api)

    return app


if __name__ == '__main__':
    app = create_app()
    start_scheduler(app)
    logging.info("Starting Birthday Wish Assistant backend on http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
