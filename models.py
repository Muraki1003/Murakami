# models.py
from datetime import datetime
from flask_login import UserMixin
from config import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    height = db.Column(db.Float, nullable=True)
    bmi_records = db.relationship('BMIRecord', backref='user', lazy=True)
    bmi_goal = db.relationship('BMIGoal', backref='user', uselist=False)

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