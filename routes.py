# routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from config import app, db
from models import User, BMIRecord, BMIGoal

def calculate_bmi(weight, height):
    """BMIを計算する関数"""
    bmi = weight / (height * height)
    return round(bmi, 1)

def get_bmi_status(bmi):
    """BMIから体型を判定する関数"""
    if bmi < 18.5:
        return "低体重", "健康的な体重を維持するため、バランスの取れた食事を心がけましょう。"
    elif 18.5 <= bmi < 25:
        return "普通体重", "健康的な体格です。この状態を維持しましょう。"
    elif 25 <= bmi < 30:
        return "肥満（1度）", "適度な運動と食事制限で改善を目指しましょう。"
    elif 30 <= bmi < 35:
        return "肥満（2度）", "専門家に相談し、生活習慣の改善を検討しましょう。"
    else:
        return "肥満（3度）", "健康リスクが高いため、医師に相談することをお勧めします。"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        height = float(request.form.get('height', 0)) / 100  # cmからmに変換
        
        if User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使用されています')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            height=height
        )
        db.session.add(user)
        db.session.commit()
        
        flash('登録が完了しました')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('ユーザー名またはパスワードが正しくありません')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/update_height', methods=['POST'])
@login_required
def update_height():
    height = float(request.form['height']) / 100  # cmからmに変換
    current_user.height = height
    db.session.commit()
    flash('身長が更新されました')
    return redirect(url_for('index'))

# routes.py内のindex関数を更新

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    today = datetime.now()
    
    # テンプレートでBMI判定を使用できるようにする
    def template_get_bmi_status(bmi):
        status, _ = get_bmi_status(bmi)
        return status
    
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = current_user.height or float(request.form.get('height', 0)) / 100
            record_date = request.form.get('record_date')
            
            if weight <= 0 or height <= 0:
                flash("正しい値を入力してください。")
                return redirect(url_for('index'))
            
            if not current_user.height:
                current_user.height = height
                db.session.commit()
            
            bmi = calculate_bmi(weight, height)
            status, advice = get_bmi_status(bmi)
            
            record = BMIRecord(
                user_id=current_user.id,
                weight=weight,
                height=height,
                bmi=bmi
            )
            
            if record_date:
                record.date = datetime.strptime(record_date, '%Y-%m-%d')
            
            db.session.add(record)
            db.session.commit()
            
            return render_template('index.html', 
                                 result={'bmi': bmi, 'status': status, 'advice': advice},
                                 records=current_user.bmi_records,
                                 goal=current_user.bmi_goal,
                                 today=today,
                                 get_bmi_status=template_get_bmi_status)
            
        except ValueError:
            flash("正しい数値を入力してください。")
            return redirect(url_for('index'))
    
    return render_template('index.html', 
                         records=current_user.bmi_records,
                         goal=current_user.bmi_goal,
                         today=today,
                         get_bmi_status=template_get_bmi_status)

@app.route('/get_bmi_data')
@login_required
def get_bmi_data():
    # 日付の昇順でデータを取得
    records = BMIRecord.query.filter_by(user_id=current_user.id)\
        .order_by(BMIRecord.date.asc())\
        .all()
    
    # 日付をフォーマットし、必要なデータのみを送信
    formatted_records = [{
        'date': record.date.strftime('%Y-%m-%d'),
        'bmi': round(record.bmi, 1),
        'weight': round(record.weight, 1)
    } for record in records]
    
    return jsonify(formatted_records)

@app.route('/set_goal', methods=['GET', 'POST'])
@login_required
def set_goal():
    if request.method == 'POST':
        target_bmi = float(request.form['target_bmi'])
        target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')
        
        goal = BMIGoal.query.filter_by(user_id=current_user.id).first()
        if goal:
            goal.target_bmi = target_bmi
            goal.target_date = target_date
        else:
            goal = BMIGoal(
                user_id=current_user.id,
                target_bmi=target_bmi,
                target_date=target_date
            )
            db.session.add(goal)
        
        db.session.commit()
        flash('目標が設定されました')
        return redirect(url_for('index'))
    
    return render_template('set_goal.html')

@app.route('/add_health_data', methods=['GET', 'POST'])
@login_required
def add_health_data():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            height = float(request.form['height']) / 100  # cmをmに変換
            weight = float(request.form['weight'])
            bmi = calculate_bmi(weight, height)
            blood_pressure_systolic = int(request.form.get('blood_pressure_systolic', 0))
            blood_pressure_diastolic = int(request.form.get('blood_pressure_diastolic', 0))
            blood_sugar = float(request.form.get('blood_sugar', 0))
            hba1c = float(request.form.get('hba1c', 0))
            cholesterol_hdl = float(request.form.get('cholesterol_hdl', 0))
            cholesterol_ldl = float(request.form.get('cholesterol_ldl', 0))
            total_cholesterol = float(request.form.get('total_cholesterol', 0))

            # 健康診断データを保存
            record = HealthCheckRecord(
                user_id=current_user.id,
                date=date,
                height=height,
                weight=weight,
                bmi=bmi,
                blood_pressure_systolic=blood_pressure_systolic,
                blood_pressure_diastolic=blood_pressure_diastolic,
                blood_sugar=blood_sugar,
                hba1c=hba1c,
                cholesterol_hdl=cholesterol_hdl,
                cholesterol_ldl=cholesterol_ldl,
                total_cholesterol=total_cholesterol
            )
            db.session.add(record)
            db.session.commit()
            flash('健康診断データを追加しました。')
        except ValueError:
            flash('正しい値を入力してください。')
        return redirect(url_for('add_health_data'))

    return render_template('add_health_data.html')

