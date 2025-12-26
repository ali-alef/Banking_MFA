import hashlib
from datetime import datetime, timedelta
import re
from flask import Flask, request, jsonify, render_template
import random
import string
import requests
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['user_database']
users_collection = db['users']
app.secret_key = 'your_secret_key_here'

BOT_TOKEN = '8375902492:AAHl2lDeh4AicDyzD8BAKRlh2YHff66TJ5s'

@app.route('/register-page')
def register_page():
    return render_template('register.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    return response

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    username = data['username']
    password = data['password']
    telegram_chat_id = data['telegram_chat_id']

    if users_collection.find_one({"username": username}):
        return jsonify({'message': 'این نام کاربری وجود دارد.'}), 400

    if len(password) < 8:
        return jsonify({'message': 'رمز عبور باید حداقل 8 کاراکتر باشد.'}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({'message': 'رمز عبور باید حداقل یک حرف بزرگ داشته باشد.'}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({'message': 'رمز عبور باید حداقل یک حرف کوچک داشته باشد.'}), 400
    if not re.search(r'\d', password):
        return jsonify({'message': 'رمز عبور باید حداقل یک عدد داشته باشد.'}), 400
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return jsonify({'message': 'رمز عبور باید حداقل یک کاراکتر ویژه داشته باشد.'}), 400

    verification_code = generate_code()
    hashed_password = hash_password(password)
    user_data = {
        'username': username,
        'password': hashed_password,
        'telegram_chat_id': telegram_chat_id,
        'verification_code': verification_code,
        'verified': False,
        'verification_code_created_at': datetime.now(),
    }

    users_collection.insert_one(user_data)

    message = f"کد تایید شما: {verification_code}"
    send_telegram_message(telegram_chat_id, message)

    return jsonify({'message': 'اطلاعات کاربری ثبت شد لطفا کد فرستاده در تلگرام را وارد کنید.'})

@app.route('/login-step1', methods=['POST'])
def login_step1():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hashed_password = hash_password(password)

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'نام کاربری اشتباه است.'})
    if user['password'] != hashed_password:
        return jsonify({'success': False, 'message': 'رمز عبور اشتباه است.'})
    if not user.get('verified', False):
        return jsonify({'success': False, 'message': 'نام کاربری تایید نشده.'})

    login_code = ''.join(random.choices(string.digits, k=6))
    users_collection.update_one({'username': username}, {'$set': {'login_code': login_code}})
    send_telegram_message(user['telegram_chat_id'], f"کد ورود شما:{login_code}")

    return jsonify({'success': True, 'message': 'Telegram code sent.'})

@app.route('/login-step2', methods=['POST'])
def login_step2():
    data = request.get_json()
    username = data.get('username')
    code = data.get('code')

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'کاربر اشتباه است.'})

    if user.get('login_code') == code:
        users_collection.update_one({'username': username}, {'$unset': {'login_code': ''}})
        send_telegram_message(user['telegram_chat_id'], "با موفقیت به پنل خود وارد شدید.")
        return jsonify({'success': True, 'message': 'Login successful!'})
    else:
        return jsonify({'success': False, 'message': 'کد اشتباه است.'})

@app.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    username = data['username']
    code_entered = data['code']

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'کاربر پیدا نشد'}), 404

    code_created_at = user.get('verification_code_created_at')
    if not code_created_at:
        return jsonify({'message': 'کد معتبر نیست.'}), 400

    now = datetime.now()
    if now - code_created_at > timedelta(minutes=2):
        return jsonify({'message': 'کد تایید منقضی شده است.'}), 400

    if user['verification_code'] == code_entered:
        users_collection.update_one(
            {'username': username},
            {'$set': {'verified': True}, '$unset': {'verification_code': '', 'verification_code_created_at': ''}}
        )
        send_telegram_message(user['telegram_chat_id'], "با موفقیت به پنل خود وارد شدید.")
        return jsonify({'message': 'اطلاعات شما کامل ثبت شد.'})
    else:
        return jsonify({'message': 'کد وارد شده اشتباه است.'}), 400

@app.route('/resend-code', methods=['POST'])
def resend_code():
    data = request.get_json()
    username = data.get('username')

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'کاربر یافت نشد.'}), 404

    new_code = generate_code()
    now = datetime.now()
    users_collection.update_one(
        {'username': username},
        {'$set': {'verification_code': new_code, 'verification_code_created_at': now}}
    )

    send_telegram_message(user['telegram_chat_id'], f"کد جدید شما: {new_code}")
    return jsonify({'message': 'کد جدید ارسال شد.'})

if __name__ == '__main__':
    app.run(debug=True)
