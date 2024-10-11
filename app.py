import time
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector  # MySQL 데이터베이스 설정을 위한 모듈
from openai import OpenAI


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 설정
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'subyou'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'chatbot'

mysql_db = MySQL(app)
CORS(app)


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


def restart_agent(num):
    from llm.react_agentbarrack import ReActAgentBarrack
    from llm import presets  

    preset_list = [presets.PRESET_A, presets.PRESET_B, presets.PRESET_C]

    agent = ReActAgentBarrack(
        presets=preset_list[num-1],
        verbose = False,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/lost_passport_qna.txt',
        name='lostpassports_qna-tool',
        description='여권분실 관련 내용에 답변을 제시해야할 때 유용합니다.',
        chunk_size=600,
        chunk_overlap=100,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_petition_info.txt',
        name='passport_petition_info-tool',
        description='여권에 민원에 대한 정보를 제시해야할 때 유용합니다.',
        chunk_size=600,
        chunk_overlap=120,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/diplomatic_list.txt',
        name='diplomatic_list-tool',
        description='영사관, 대사관에 대한 정보를 제시해야할 때 유용합니다.',
        chunk_size=350,
        chunk_overlap=50,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_laws_links.txt',
        name='passport_laws_links-tool',
        description='여권에 관련된 법률 링크를 제시해야할 때 유용합니다.',
        chunk_size=350,
        chunk_overlap=50,
    )
    
    agent.make_agent()
       
    return agent

# @app.route('/')
# def main():
#     session.clear()
#     chat_agent1 = restart_agent(1)
#     chat_agent2 = restart_agent(2)
#     chat_agent3 = restart_agent(3)

#     session['chat_agent1'] = chat_agent1
#     session['chat_agent2'] = chat_agent2
#     session['chat_agent3'] = chat_agent3

#     userid = request.args.get('userid')
#     # URL에 userid가 있으면 세션에 저장
#     if userid:
#         session['userid'] = userid
#     else:
#         return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400
#     return render_template('main.html', userid=userid)

@app.route('/survey/chat1')
def chatbot_type1():
    session.clear()
    chat_agent = restart_agent(1)
    session['chat_agent1'] = chat_agent

    userid = request.args.get('userid')

    if userid:
        session['userid'] = userid
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400

    return render_template('main.html', userid=userid) 

@app.route('/survey/type2')
def chatbot_type2():
    session.clear()
    session['chat_agent2'] = restart_agent(2) 

    userid = request.args.get('userid')
    # URL에 userid가 있으면 세션에 저장
    if userid:
        session['userid'] = userid
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400

    return render_template('type2.html', userid=userid)  # 메인 페이지 렌더링 시 사용자 이름을 전달

@app.route('/survey/type3')
def chatbot_type3():
    session.clear()
    session['chat_agent3'] = restart_agent(3) 

    userid = request.args.get('userid')
    # URL에 userid가 있으면 세션에 저장
    if userid:
        session['userid'] = userid
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400

    return render_template('type3.html', userid=userid)  # 메인 페이지 렌더링 시 사용자 이름을 전달

conversation_types = {
    1: 'conv1ID',
    2: 'conv2ID',
    3: 'conv3ID'
}


@app.route('/api/botResponse/<int:chatbot_number>', methods=['POST'])
def bot_response(chatbot_number):    
    userid = session.get('userid')
    print(userid)

    if not userid:
        return jsonify({'error': 'User ID not found in session'}), 400

    data = request.json
    user_message = data.get('message')

    if chatbot_number == 1:
        chat_agent = session['chat_agent1']
    elif chatbot_number == 2:
        chat_agent = session['chat_agent2']
    elif chatbot_number == 3:
        chat_agent = session['chat_agent3']
    else: 
        return jsonify({'error': 'Invalid chatbot number'}), 400

    
    response = chat_agent.invoke_agent(user_message)
    print(response)
    conn = mysql_db.connection
    cur = conn.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
    
    conv_type = conversation_types[chatbot_number]
    if conv_type not in session:
        cur.execute("INSERT INTO conversations (user_id, chat_type) VALUES (%s, %s)", (userid, conv_type, ))
        conversation_id = cur.lastrowid
        session[conv_type] = conversation_id
    else:
        conversation_id = session[conv_type]

    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
        (conversation_id, 'user', user_message))
    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
                (conversation_id, 'bot', response))

    cur.close()
    conn.commit()

    return jsonify({'response': response})


@app.route('/api/chatReload/<int:chatbot_number>', methods=['POST'])
def chat_reload(chatbot_number):
    print(session)

    if chatbot_number not in [1, 2, 3]:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    session.pop(conversation_types[chatbot_number], None)

    if chatbot_number == 1:
        session['chat_agent1'] = restart_agent(chatbot_number)
    elif chatbot_number == 2:
        session['chat_agent2'] = restart_agent(chatbot_number)
    elif chatbot_number == 3:
        session['chat_agent3'] = restart_agent(chatbot_number)
    
    print(session)
    return '', 204

@app.route('/reset_session', methods=['POST'])
def reset_session():
    session.clear()  # 세션을 초기화합니다.
    return '', 204  # No Content 응답


if __name__ == '__main__':
    
    app.run(debug=True)


