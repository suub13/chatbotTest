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
app.config['MYSQL_HOST'] = 'mysql_db'
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


chat_agents = dict()

@app.route('/survey/type<int:typeNum>')
def chatbot_type(typeNum):
    session.clear()

    userid = request.args.get('userid')

    chat_agent = restart_agent(typeNum)

    if userid:
        session['userid'] = userid
        if userid not in chat_agents:
            chat_agents[userid] = {}
        chat_agents[userid][f'chat_agent{typeNum}'] = chat_agent
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400

    return render_template(f'type{typeNum}.html', userid=userid) 


conversation_types = {
    1: 'conv1',
    2: 'conv2',
    3: 'conv3'
}

@app.route('/api/userMessage<int:chatbot_number>', methods=['POST'])
def user_message(chatbot_number):    
    userid = session.get('userid')

    user_message = request.json.get('message')

    # DB연결
    conn = mysql_db.connection
    cur = conn.cursor()
    
    conv_type = conversation_types[chatbot_number]
    if conv_type not in session:
        cur.execute("INSERT INTO conversations (user_id, chat_type) VALUES (%s, %s)", (userid, conv_type, ))
        conversation_id = cur.lastrowid
        session[conv_type] = conversation_id
        session.modified=True

    else: 
        conversation_id = session.get(conv_type)

    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
        (conversation_id, 'user', user_message))
    
    cur.close()
    conn.commit()
    
    return '', 204



@app.route('/api/botResponse<int:chatbot_number>', methods=['POST'])
def bot_response(chatbot_number):    
    userid = session.get('userid')

    if not userid:
        return jsonify({'error': 'User ID not found in session'}), 400
    
    # 사용자 message 가져오기
    user_message = request.json.get('message')

    # agent 가져오기
    chat_agent = chat_agents[userid][f'chat_agent{chatbot_number}']
    
    response = chat_agent.invoke_agent(user_message)

    # DB연결
    conn = mysql_db.connection
    cur = conn.cursor()
    
    # session에 conv_type: conversation_id로 되어 있음.
    try: 
        conv_type = conversation_types[chatbot_number] # conv1, conv2, conv3 중 
        conversation_id = session.get(conv_type)
        if conversation_id == None:
            cur.execute(""" SELECT id FROM conversations WHERE user_id = %s AND chat_type = %s 
            ORDER BY id DESC LIMIT 1;""", (userid, conv_type))
            result = cur.fetchone()
            conversation_id = result[0]

        cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
                    (conversation_id, 'bot', response))
    except:
        return jsonify({'error': 404})
    finally:
        cur.close()
        conn.commit()

    return jsonify({'response': response})


@app.route('/api/chatReload/<int:chatbot_number>', methods=['POST'])
def chat_reload(chatbot_number):

    if chatbot_number not in [1, 2, 3]:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    userid = session.get('userid')

    chat_agents[userid][f'chat_agent{chatbot_number}'] = restart_agent(chatbot_number)

    return '', 204


@app.route('/reset_session', methods=['POST'])
def reset_session():
    session.clear()  # 세션을 초기화합니다.
    return '', 204  # No Content 응답


if __name__ == '__main__':
    app.run(debug=True)


