# init_db.py
from config import app, db
from models import User, BMIRecord, BMIGoal

if __name__ == '__main__':
    with app.app_context():
        print("データベースを初期化しています...")
        db.drop_all()  # 既存のテーブルを削除
        db.create_all()  # テーブルを新規作成
        print("データベースの初期化が完了しました")