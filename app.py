import time
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'your_secret_key'

CORS(app)

from flask import send_from_directory

base_url = "https://1f96-58-122-202-175.ngrok-free.app/"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/survey/type<int:typeNum>')
def render_chatbot_page(typeNum):
    userid = request.args.get('userid')
    
    if userid:
        if typeNum in [1,2,3]:
            return render_template(f'type{typeNum}in.html', userid=userid)
        else:
            return render_template(f'type{typeNum-3}out.html', userid=userid)
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400
    


conversation_types = {
    1: 'conv1',
    2: 'conv2',
    3: 'conv3',
    4: 'conv4',
    5: 'conv5',
    6: 'conv6'
}

import requests
def api_invoke(base_url, category, location, question, thread_id):

    endpoint = f"{base_url}/invoke/{category}_{location}"
    params = {
        "category": category,
        "location": location,
        "question": question,
        "thread_id": thread_id,
    }
    response = requests.post(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)


@app.route('/api/botResponse<int:typeNum>', methods=['POST'])
def bot_response(typeNum):    
    userid = request.json.get('userid')


    bot_types = ['A_IN', 'B_IN', 'C_IN', 'A_OUT', 'B_OUT', 'C_OUT']
    category, location = bot_types[typeNum-1].split('_')

    if not userid:
        return jsonify({'error': 'User ID not found in session'}), 400
    
    # 사용자 message 가져오기
    user_message = request.json.get('message')

    rv = api_invoke(base_url, category, location, user_message, userid)
    response = rv['response']
    message_id = rv['message_id']

    return jsonify({'response': response, 'message_id': message_id})



@app.route('/api/chatReload/<int:typeNum>', methods=['POST'])
def chat_reload(typeNum):
    if typeNum not in range(1, 7):
        return jsonify({'error': 'Invalid chatbot number'}), 400

    userid = request.json.get('userid')
    bot_types = ['A_IN', 'B_IN', 'C_IN', 'A_OUT', 'B_OUT', 'C_OUT']
    category, location = bot_types[typeNum - 1].split('_')

    response = api_clear_thread_memory(base_url, category, location, userid)

    # 결과 처리
    if response.get('response') == 1:
        return '', 204
    return jsonify({'error': 'Thread memory clearance unsuccessful'}), 500


def api_clear_thread_memory(base_url, category, location, thread_id):
    endpoint = f"{base_url}/clear_thread_memory"
    params = {
        "category": category,
        "location": location,
        "thread_id": thread_id,
    }
    response = requests.post(endpoint, params=params).json()
    
    return response


@app.route('/api/feedback', methods=['POST'])
def update_feedback():
    data = request.json
    message_id = data.get('message_id')
    feedback = data.get('feedback')

    endpoint = f"{base_url}/update_feedback"
    params = {
        "message_id": message_id,
        "thumbs": feedback,
    }
    response = requests.post(endpoint, params=params).json()

    if response.get('response') == 1:
        return response
    else:
        return jsonify({'error': 'feedback update unsuccessful'}), 500


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)


