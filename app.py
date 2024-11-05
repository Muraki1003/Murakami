# app.py
from config import app, db, login_manager
from models import User
from routes import *

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))