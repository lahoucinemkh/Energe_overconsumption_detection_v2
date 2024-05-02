import os
import sys
import logging
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"

log_dir = "logs"
log_filepath = os.path.join(log_dir,"running_logs.log")
os.makedirs(log_dir, exist_ok=True)


logging.basicConfig(
    level= logging.INFO,
    format= logging_str,

    handlers=[
        logging.FileHandler(log_filepath),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("anomalyDetectorLogger")


app = Flask(__name__)
app.config['SECRET_KEY'] = '9282ea5875a48a8b8c13893b'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"
from anomalyDetector import routes



