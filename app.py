# app.py
from flask import Flask, render_template, request
import json

app = Flask(__name__)

def calculate_bmi(weight, height):
    """
    BMIを計算する関数
    weight: 体重(kg)
    height: 身長(m)
    """
    bmi = weight / (height * height)
    return round(bmi, 1)

def get_bmi_status(bmi):
    """
    BMIから体型を判定する関数
    """
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height']) / 100  # cmからmに変換
            
            if weight <= 0 or height <= 0:
                return render_template('index.html', error="正しい値を入力してください。")
            
            bmi = calculate_bmi(weight, height)
            status, advice = get_bmi_status(bmi)
            
            result = {
                'bmi': bmi,
                'status': status,
                'advice': advice
            }
            return render_template('index.html', result=result)
        except ValueError:
            return render_template('index.html', error="正しい数値を入力してください。")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)