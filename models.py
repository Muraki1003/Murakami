# models.py
from datetime import datetime
from flask_login import UserMixin
from config import db

class MealRecord(db.Model):
    __tablename__ = 'meal_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meal_type = db.Column(db.String(20), nullable=False)  # 朝食、昼食、夕食、間食
    
    # 画像解析結果
    dish_name = db.Column(db.String(100))
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    fat = db.Column(db.Float)
    carbohydrate = db.Column(db.Float)
    
    # 画像パス
    image_path = db.Column(db.String(200))
    location = db.Column(db.String(50))  # 画像内の位置情報

    # その他の栄養情報
    fiber = db.Column(db.Float)
    sugar = db.Column(db.Float)
    sodium = db.Column(db.Float)

    # メモ
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'meal_type': self.meal_type,
            'dish_name': self.dish_name,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbohydrate': self.carbohydrate,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium,
            'notes': self.notes,
            'image_path': self.image_path,
            'location': self.location
        }

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    height = db.Column(db.Float, nullable=True)
    bmi_records = db.relationship('BMIRecord', backref='user', lazy=True)
    bmi_goal = db.relationship('BMIGoal', backref='user', uselist=False)
    meal_records = db.relationship('MealRecord', backref='user', lazy=True)  # 追加

class BMIRecord(db.Model):
    __tablename__ = 'bmi_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'bmi': round(self.bmi, 1),
            'weight': self.weight
        }

class BMIGoal(db.Model):
    __tablename__ = 'bmi_goal'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_bmi = db.Column(db.Float, nullable=False)
    target_date = db.Column(db.DateTime, nullable=False)
    
from config import db

class HealthCheckRecord(db.Model):
    __tablename__ = 'health_check_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    height = db.Column(db.Float)  # 身長 (m)
    weight = db.Column(db.Float)  # 体重 (kg)
    bmi = db.Column(db.Float)  # BMI
    blood_pressure_systolic = db.Column(db.Integer)  # 収縮期血圧
    blood_pressure_diastolic = db.Column(db.Integer)  # 拡張期血圧
    blood_sugar = db.Column(db.Float)  # 血糖値
    hba1c = db.Column(db.Float)  # HbA1c
    cholesterol_hdl = db.Column(db.Float)  # HDLコレステロール
    cholesterol_ldl = db.Column(db.Float)  # LDLコレステロール
    total_cholesterol = db.Column(db.Float)  # 総コレステロール

    user = db.relationship('User', back_populates='health_records')

class User(db.Model):
    # 既存フィールド
    health_records = db.relationship('HealthCheckRecord', back_populates='user', cascade='all, delete-orphan')