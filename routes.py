# routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import requests
import json
from flask import session

from config import app, db
from models import User, BMIRecord, BMIGoal, MealRecord

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

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



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_food_image(image_path):
    try:
        url = "http://localhost:11434/api/generate"
        
        with open(image_path, "rb") as image_file:
            import base64
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        data = {
            "model": "llava",
            "prompt": "Analyze this food image and return the following information in JSON format. For numeric values, use numbers only without units:\n"
                     "{\n"
                     "  \"dishes\": [\n"
                     "    {\n"
                     "      \"dish_name\": \"name of the dish\",\n"
                     "      \"cuisine_type\": \"type of cuisine (e.g., Japanese, Italian, Chinese)\",\n"
                     "      \"calories\": estimated calories (number only),\n"
                     "      \"nutrients\": {\n"
                     "        \"protein\": protein in grams (number only),\n"
                     "        \"fat\": fat in grams (number only),\n"
                     "        \"carbohydrate\": carbohydrates in grams (number only),\n"
                     "        \"dietary_fiber\": dietary fiber in grams (number only),\n"
                     "        \"vitamins\": \"main vitamins present\",\n"
                     "        \"minerals\": \"main minerals present\"\n"
                     "      },\n"
                     "      \"ingredients\": [\"list of main ingredients\"],\n"
                     "      \"cooking_method\": \"main cooking method used\",\n"
                     "      \"location\": \"position in image (e.g., top-left, center, bottom-right)\",\n"
                     "      \"health_notes\": \"health-related notes, nutritional highlights\"\n"
                     "    }\n"
                     "  ]\n"
                     "}\n"
                     "Return only the JSON without any additional formatting or markdown.",
            "images": [image_data],
            "stream": False
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            response_text = response.text
            print("Raw API Response:", response_text)

            try:
                response_lines = response_text.strip().split('\n')
                last_line = response_lines[-1]
                response_json = json.loads(last_line)
                
                if 'response' in response_json:
                    try:
                        content = response_json['response']
                        content = content.replace('```json', '').replace('```', '').strip()
                        print("Cleaned content:", content)

                        # JSON文字列をパースする前に数値の単位を削除
                        import re
                        content = re.sub(r'(\d+)g', r'\1', content)
                        print("Content after unit removal:", content)
                        
                        result = json.loads(content)
                        dishes = result.get('dishes', [result]) if isinstance(result, dict) else [result]
                        
                        normalized_dishes = []
                        for dish in dishes:
                            nutrients = dish.get('nutrients', {})
                            notes = []
                            if dish.get('cuisine_type'):
                                notes.append(f"Cuisine: {dish['cuisine_type']}")
                            if 'cooking_method' in dish:
                                notes.append(f"Cooking Method: {dish['cooking_method']}")
                            if 'ingredients' in dish:
                                notes.append(f"Ingredients: {', '.join(dish['ingredients'])}")
                            if nutrients.get('vitamins'):
                                if isinstance(nutrients['vitamins'], list):
                                    notes.append(f"Vitamins: {', '.join(nutrients['vitamins'])}")
                                else:
                                    notes.append(f"Vitamins: {nutrients['vitamins']}")
                            if nutrients.get('minerals'):
                                if isinstance(nutrients['minerals'], list):
                                    notes.append(f"Minerals: {', '.join(nutrients['minerals'])}")
                                else:
                                    notes.append(f"Minerals: {nutrients['minerals']}")
                            if 'health_notes' in dish:
                                notes.append(f"Health Notes: {dish['health_notes']}")
                            
                            normalized_dish = {
                                "dish_name": str(dish.get('dish_name', 'Unknown dish')),
                                "calories": clean_numeric_value(dish.get('calories', 0)),
                                "protein": clean_numeric_value(nutrients.get('protein', 0)),
                                "fat": clean_numeric_value(nutrients.get('fat', 0)),
                                "carbohydrate": clean_numeric_value(nutrients.get('carbohydrate', 0)),
                                "fiber": clean_numeric_value(nutrients.get('dietary_fiber', 0)),
                                "location": str(dish.get('location', 'unknown')),
                                "notes": "\n".join(notes)
                            }
                            normalized_dishes.append(normalized_dish)
                        
                        return normalized_dishes
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing content as JSON: {e}")
                        print(f"Content that failed to parse: {content}")
                        return [create_default_analysis()]
                else:
                    print("No 'response' key in API response")
                    return [create_default_analysis()]
                    
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Error processing API response: {e}")
                return [create_default_analysis()]
        else:
            print(f"API request failed with status code: {response.status_code}")
            return [create_default_analysis()]
            
    except Exception as e:
        print(f"Error analyzing image: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(traceback.format_exc())
        return [create_default_analysis()]

def clean_numeric_value(value):
    """数値から単位を取り除き、float型に変換する"""
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        # 数字部分のみを抽出
        import re
        numeric = re.search(r'(\d+(?:\.\d+)?)', value)
        return float(numeric.group(1)) if numeric else 0.0
    return 0.0

def create_default_analysis():
    """
    デフォルトの解析結果を生成
    """
    return {
        "dish_name": "Unknown dish",
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbohydrate": 0,
        "fiber": 0,
        "location": "unknown",
        "notes": "Analysis failed"
    }

@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    if request.method == 'POST':
        try:
            # セッションから最後にアップロードされた画像情報を取得
            last_uploaded = session.get('last_uploaded_image')
            if not last_uploaded:
                flash('画像がアップロードされていません')
                return redirect(request.url)

            file_path = last_uploaded['path']
            filename = last_uploaded['filename']
            
            # 'uploads' ディレクトリへの相対パスを作成
            relative_path = 'uploads/' + filename
            
            dish_count = int(request.form.get('dish_count', 1))
            
            # 各料理について記録を保存
            for i in range(dish_count):
                meal_record = MealRecord(
                    user_id=current_user.id,
                    meal_type=request.form.get('meal_type', '未分類'),
                    image_path=relative_path,  # 修正された相対パス
                    dish_name=request.form.get(f'dish_name_{i}', 'Unknown dish'),
                    calories=float(request.form.get(f'calories_{i}', 0)),
                    protein=float(request.form.get(f'protein_{i}', 0)),
                    fat=float(request.form.get(f'fat_{i}', 0)),
                    carbohydrate=float(request.form.get(f'carbs_{i}', 0)),
                    fiber=float(request.form.get(f'fiber_{i}', 0)),
                    location=request.form.get(f'location_{i}', 'unknown'),
                    notes=request.form.get(f'notes_{i}', '')
                )
                
                db.session.add(meal_record)
            
            db.session.commit()
            
            # セッションから画像情報をクリア
            session.pop('last_uploaded_image', None)
            
            flash('食事記録が保存されました')
            return redirect(url_for('meal_history'))
        
        except Exception as e:
            print(f"Error saving meal record: {e}")
            flash('食事記録の保存中にエラーが発生しました')
            return redirect(request.url)
                
    return render_template('add_meal.html')

@app.route('/meal_history')
@login_required
def meal_history():
    meals = MealRecord.query.filter_by(user_id=current_user.id)\
        .order_by(MealRecord.date.desc())\
        .all()
    return render_template('meal_history.html', meals=meals)





@app.route('/analyze_image', methods=['POST'])
@login_required
def analyze_image():
    if 'food_image' not in request.files:
        return jsonify({'error': '画像がありません'}), 400
            
    file = request.files['food_image']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
            
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            
            # アップロードディレクトリの作成（static/uploads/）
            upload_folder = os.path.join('static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            # ファイルを保存
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # ファイル情報をセッションに保存
            session['last_uploaded_image'] = {
                'filename': filename,
                'path': file_path
            }
            
            # 画像解析
            analysis_results = analyze_food_image(file_path)
            
            return jsonify(analysis_results)
        
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return jsonify({'error': '画像の解析中にエラーが発生しました'}), 500
    else:
        return jsonify({'error': '許可されていないファイル形式です'}), 400
