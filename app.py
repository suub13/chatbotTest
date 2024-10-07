import time
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector  # MySQL 데이터베이스 설정을 위한 모듈
from openai import OpenAI
from llm import agentbarrack


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 설정
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'subyou'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'chatbot'

mysql_db = MySQL(app)
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})


def run_sql_script(script_path):
    with open(script_path, 'r') as file:
        sql_script = file.read()

    conn = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']

    )

    cursor = conn.cursor()
    try:
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

run_sql_script('setup.sql')

chat_agent1 = None
chat_agent2 = None
chat_agent3 = None

# conn = create_connection()


def restart_agent(num):
    from llm.react_agentbarrack import ReActAgentBarrack
    from llm import presets  

    preset_list = [presets.PRESET_A, presets.PRESET_B, presets.PRESET_C]

    agent = ReActAgentBarrack(
    presets=preset_list[num-1],
    verbose = False,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/qna.txt',
        name='qna-relevant_statutory_provisions-tool',
        description='민원 질문에 대한 해결방법과 근거법령을 제시해야할 때 유용합니다.',
        )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/link.txt',
        name='statute_links-tool',
        description='근거법령의 링크를 제시해야할 때 유용합니다.',
        )
    
    agent.make_tool_from_DocRetriever(
        doc_path='assets/lostpassports_qna.txt',
        name='lost_passports_qna-tool',
        description='여권분실 관련 내용에 답변을 제시해야할 때 유용합니다.',
        )
    
    agent.make_tool_from_DocRetriever(
        doc_path='assets/diplomatic_list.txt',
        name='diplomatic_list-tool',
        description='영사관, 대사관에 대한 정보를 제시해야할 때 유용합니다.',
        )

    agent.make_agent()
       
    return agent



@app.route('/')
def main():
    # username = session.get('username')  # 로그인된 사용자 이름을 세션에서 가져옴
    # return render_template('main.html', username=username)  # 메인 페이지 렌더링 시 사용자 이름을 전달
    session.clear()
    return render_template('main.html')  # 메인 페이지 렌더링 시 사용자 이름을 전달


@app.route('/api/botResponse/<int:chatbot_number>', methods=['POST'])
def bot_response(chatbot_number):
    data = request.json
    user_message = data.get('message')

    if chatbot_number == 1:
        chat_agent = chat_agent1
    elif chatbot_number == 2:
        chat_agent = chat_agent2
    elif chatbot_number == 3:
        chat_agent = chat_agent3
    else: 
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    response = chat_agent.invoke_agent(user_message)
    print(response)
    conn = mysql_db.connection
    cur = conn.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
    
    conversation_types = {
        1: 'conv1ID',
        2: 'conv2ID',
        3: 'conv3ID'
    }

    conv_type = conversation_types[chatbot_number]
    print(session)
    if conv_type not in session:
        # user_id = session['user_id']
        cur.execute("INSERT INTO conversations (chat_type) VALUES (%s)", (conv_type, ))
        conversation_id = cur.lastrowid
        session[conv_type] = conversation_id
    else:
        conversation_id = session[conv_type]

    cur.execute("SELECT * FROM conversations;")
    convs = cur.fetchall()
    print(convs)
    print(conversation_id)

    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
        (conversation_id, 'user', user_message))
    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
                (conversation_id, 'bot', response))

    cur.close()
    conn.commit()

    return jsonify({'response': response})


@app.route('/api/chatReload/<int:chatbot_number>', methods=['GET'])
def chat_reload(chatbot_number):

    if chatbot_number == 1:
        chat_agent1 = restart_agent(chatbot_number)
    elif chatbot_number == 2:
        chat_agent2 = restart_agent(chatbot_number)
    elif chatbot_number == 3:
        chat_agent3 = restart_agent(chatbot_number)
    else: 
        return jsonify({'error': 'Invalid chatbot number'}), 400
    


@app.route('/check_username')
def check_username():
    username = request.args.get('username')
    cur = mysql_db.connection.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        return {'exists': existing_user is not None}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cur.close()


# @app.route('/reset_session', methods=['POST'])
# def reset_session():
#     session.clear()  # 세션을 초기화합니다.
#     return '', 204  # No Content 응답


if __name__ == '__main__':
    chat_agent1 = restart_agent(1)
    chat_agent2 = restart_agent(2)
    chat_agent3 = restart_agent(3)
    
    app.run(debug=True)
    session.clear()
