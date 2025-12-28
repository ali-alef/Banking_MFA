from flask import Flask, request, jsonify
from datetime import datetime
import hashlib

# Initialize blockchain
auth_blockchain = AuthBlockchain()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data['username']
    password = data['password']
    telegram_chat_id = data['telegram_chat_id']

    # Existing registration logic...
    
    # Record registration event in blockchain
    auth_blockchain.add_auth_event(
        username=username,
        event_type='user_registered',
        ip_address=request.remote_addr,
        device_info=request.headers.get('User-Agent')
    )
    
    return jsonify({'message': 'User registered successfully.'})


@app.route('/login-step1', methods=['POST'])
def login_step1():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hashed_password = hash_password(password)

    user = users_collection.find_one({'username': username})
    
    if not user:
        # Record failed login attempt in blockchain
        auth_blockchain.add_auth_event(
            username=username,
            event_type='login_failed_user_not_found',
            ip_address=request.remote_addr,
            device_info=request.headers.get('User-Agent')
        )
        return jsonify({'success': False, 'message': 'نام کاربری اشتباه است.'})
    
    if user['password'] != hashed_password:
        # Record wrong password attempt
        auth_blockchain.add_auth_event(
            username=username,
            event_type='login_failed_wrong_password',
            ip_address=request.remote_addr,
            device_info=request.headers.get('User-Agent')
        )
        return jsonify({'success': False, 'message': 'رمز عبور اشتباه است.'})
    
    # Generate OTP
    login_code = ''.join(random.choices(string.digits, k=6))
    users_collection.update_one({'username': username}, {'$set': {'login_code': login_code}})
    send_telegram_message(user['telegram_chat_id'], f"کد ورود شما: {login_code}")
    
    # Record successful step 1
    auth_blockchain.add_auth_event(
        username=username,
        event_type='login_step1_success_otp_sent',
        ip_address=request.remote_addr,
        device_info=request.headers.get('User-Agent')
    )
    
    return jsonify({'success': True, 'message': 'Telegram code sent.'})


@app.route('/login-step2', methods=['POST'])
def login_step2():
    data = request.get_json()
    username = data.get('username')
    code = data.get('code')

    user = users_collection.find_one({'username': username})
    
    if user.get('login_code') == code:
        users_collection.update_one({'username': username}, {'$unset': {'login_code': ''}})
        
        # Record successful login
        auth_blockchain.add_auth_event(
            username=username,
            event_type='login_complete_success',
            ip_address=request.remote_addr,
            device_info=request.headers.get('User-Agent')
        )
        
        return jsonify({'success': True, 'message': 'Login successful!'})
    else:
        # Record wrong OTP
        auth_blockchain.add_auth_event(
            username=username,
            event_type='login_step2_failed_wrong_otp',
            ip_address=request.remote_addr,
            device_info=request.headers.get('User-Agent')
        )
        return jsonify({'success': False, 'message': 'کد اشتباه است.'})
