# config.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bmi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db():
    db_path = os.path.join(app.instance_path, 'bmi.db')
    
    # インスタンスフォルダが存在しない場合は作成
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
    
    # データベースが存在しない場合は初期化
    if not os.path.exists(db_path):
        with app.app_context():
            # モデルをインポート（循環インポートを避けるため、ここでインポート）
            from models import User, BMIRecord, BMIGoal
            print("データベースを初期化しています...")
            db.create_all()
            print("データベースの初期化が完了しました")

# アプリケーション起動時にデータベースを初期化
init_db()