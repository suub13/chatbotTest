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

from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


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
        preset=preset_list[num-1],
        verbose = False,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/car_qna.txt',
        name='car_qna-tool',
        description='자동차 등록 또는 말소 질문에 대한 답변을 제시해야할 때 유용합니다.',
        chunk_size=400,
        chunk_overlap=75,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/car_petition_info.txt',
        name='car_petition_info-tool',
        description='자동차의 등록, 폐차의 신청 방법을 제시해야할 때 유용합니다.',
        chunk_size=800,
        chunk_overlap=120,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/car_registrar_list.txt',
        name='car_registrar_list-tool',
        description='자동차등록소의 주소와 전화번호를 제시해야할 때 유용합니다.',
        chunk_size=150,
        chunk_overlap=30,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/car_junkyard_list.txt',
        name='car_junkyard_list-tool',
        description='폐차장의 주소와 전화번호를 제시해야할 때 유용합니다.',
        chunk_size=350,
        chunk_overlap=50,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/car_laws_links.txt',
        name='car_laws_links-tool',
        description='자동차에 관련된 법률 링크를 제시해야할 때 유용합니다.',
        chunk_size=250,
        chunk_overlap=50,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_qna.txt',
        name='passports_qna-tool',
        description='여권 관련 질문에 대한 답변을 제시해야할 때 유용합니다.',
        chunk_size=600,
        chunk_overlap=100,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_petition_info.txt',
        name='passport_petition_info-tool',
        description='여권 최초 발급, 여권 재발급, 긴급여권, 여권 분실 신청 방법을 제시해야할 때 유용합니다.',
        chunk_size=600,
        chunk_overlap=120,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_diplomatic_list.txt',
        name='diplomatic_list-tool',
        description='영사관, 대사관에 대한 정보를 제시해야할 때 유용합니다.',
        chunk_size=350,
        chunk_overlap=50,
    )

    agent.make_tool_from_DocRetriever(
        doc_path='assets/passport_laws_links.txt',
        name='passport_laws_links-tool',
        description='여권에 관련된 법률 링크를 제시해야할 때 유용합니다.',
        chunk_size=250,
        chunk_overlap=50,
    )
    
    agent.make_agent()
       
    return agent


chat_agents = dict()

@app.route('/survey/type<int:typeNum>')
def render_chatbot_page(typeNum):
    print("surve/type")
    # session.clear()
    userid = request.args.get('userid')
    
    if userid:
        session['userid'] = userid
        session['typeNum'] = typeNum
        return render_template(f'type{typeNum}.html', userid=userid)
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400
    

@app.route('/create_agent', methods=['POST'])
def create_agent_route():
    result = create_chat_agent()
    return result


def create_chat_agent():
    userid = session['userid']
    typeNum = session['typeNum']
    print(userid, typeNum)

    # Check for necessary data
    if not userid or not typeNum:
        return jsonify({'error': 'Missing userid or typeNum'}), 400
    
    # Create or restart the chat agent
    chat_agent = restart_agent(typeNum)
    
    # Store the agent in chat_agents (based on userid and typeNum)
    if userid not in chat_agents:
        chat_agents[userid] = {}
    
    chat_agents[userid][f'chat_agent{typeNum}'] = chat_agent

    # Return a success message
    return jsonify({'message': 'Chat agent created successfully'}), 200


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

    print(chatbot_number, conv_type, session)
    
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
    print(chat_agent.get_chat_history())
    
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
        message_id = cur.lastrowid  # Get the ID of the newly inserted message
    except:
        return jsonify({'error': 404})
    finally:
        cur.close()
        conn.commit()

    return jsonify({'response': response, 'message_id': message_id})



@app.route('/api/chatReload/<int:chatbot_number>', methods=['POST'])
def chat_reload(chatbot_number):

    if chatbot_number not in [1, 2, 3]:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    userid = session.get('userid')

    conv_type = conversation_types[chatbot_number]
    session.pop(conv_type, None)

    chat_agents[userid][f'chat_agent{chatbot_number}'] = restart_agent(chatbot_number)

    return '', 204


@app.route('/api/feedback', methods=['POST'])
def update_feedback():
    data = request.json
    message_id = data.get('message_id')
    feedback = data.get('feedback')

    if not message_id or not feedback:
        return jsonify({'error': 'Missing message ID or feedback'}), 400

    # Update the feedback in the database
    conn = mysql_db.connection
    cur = conn.cursor()
    
    feedback_value = 1 if feedback == 'up' else -1

    try:
        cur.execute("UPDATE messages SET feedback = %s WHERE id = %s", (feedback_value, message_id))
        conn.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

    return jsonify({'message': 'Feedback updated successfully'}), 200


@app.route('/api/feedback/remove', methods=['POST'])
def remove_feedback():
    data = request.json
    message_id = data.get('message_id')

    if not message_id:
        return jsonify({'error': 'Missing message ID'}), 400

    # Remove the feedback (set it to NULL or another suitable value)
    conn = mysql_db.connection
    cur = conn.cursor()

    try:
        cur.execute("UPDATE messages SET feedback = NULL WHERE id = %s", (message_id,))
        conn.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

    return jsonify({'message': 'Feedback removed successfully'}), 200


@app.route('/get_userid')
def get_userid():
    # Check if userid is in session
    userid = session.get('userid')
    return f"User ID in session: {userid}" if userid else "No User ID found in session."


@app.route('/reset_session', methods=['POST'])
def reset_session():
    session.clear()  # 세션을 초기화합니다.
    return '', 204  # No Content 응답


if __name__ == '__main__':
    app.run(debug=True)


