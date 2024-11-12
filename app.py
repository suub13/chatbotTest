import time
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector  # MySQL 데이터베이스 설정을 위한 모듈
from openai import OpenAI
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

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
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
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

    preset_list = [presets.PRESET_A_IN, presets.PRESET_B_IN, presets.PRESET_C_IN, presets.PRESET_A_OUT, presets.PRESET_B_OUT, presets.PRESET_C_OUT]

    agent = ReActAgentBarrack(
        preset=preset_list[num-1],
        verbose = False,
    )

    if num in [1,2,3]:
        agent.make_tool_from_ClosestFinder(
            preset=presets.TOOL_PRESET_AGENCY,
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
            doc_path='assets/passport_agency_list.txt',
            name='diplomatic_list-tool',
            description='한국에 있을 경우 여권사무대행기관에 대한 정보를 제시해야할 때 유용합니다.',
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
    else:
        agent.make_tool_from_ClosestFinder(
            preset=presets.TOOL_PRESET_DIPLOMATIC,
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
            description='한국 이외의 나라에 있을 경우, 영사관 또는 대사관에 대한 정보를 제시해야할 때 유용합니다.',
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
    userid = request.args.get('userid')
    
    if userid:
        if typeNum in [1,2,3]:
            return render_template(f'type{typeNum}in.html', userid=userid)
        else:
            return render_template(f'type{typeNum-3}out.html', userid=userid)
    else:
        return jsonify({'error': '제공된 링크를 통해 접속해 주세요.'}), 400
    

@app.route('/create_agent', methods=['POST'])
def create_agent_route():
    # Get userid and typeNum from the request JSON body
    data = request.get_json()
    userid = data.get('userid')
    typeNum = data.get('typeNum')
    
    result = create_chat_agent(userid, typeNum) 

    return result


def create_chat_agent(userid, typeNum):

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

@app.route('/api/userMessage<int:typeNum>', methods=['POST'])
def user_message(typeNum):    
    userid = request.json.get('userid')
    user_message = request.json.get('message')

    # DB연결
    conn = mysql_db.connection
    cur = conn.cursor()
    
    conv_type = conversation_types[typeNum]
    conv_id = request.json.get('conv_id')
    
    if conv_id is None:
        cur.execute("INSERT INTO conversations (user_id, chat_type) VALUES (%s, %s)", (userid, conv_type, ))
        conv_id = cur.lastrowid

    cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
        (conv_id, 'user', user_message))
    
    cur.close()
    conn.commit()
    
    return jsonify({'conv_id': conv_id}), 200



@app.route('/api/botResponse<int:typeNum>', methods=['POST'])
def bot_response(typeNum):    
    userid = request.json.get('userid')

    if not userid:
        return jsonify({'error': 'User ID not found in session'}), 400
    
    # 사용자 message 가져오기
    user_message = request.json.get('message')

    # agent 가져오기
    chat_agent = chat_agents[userid][f'chat_agent{typeNum}']
    response = chat_agent.invoke_agent(user_message)

    if response.strip() == "":
        response = "죄송합니다. 말씀해주신 내용을 이해하지 못 했습니다. 조금 더 구체적인 상황 또는 위치 등의 정보를 알려주실 수 있으신가요?"

    # DB연결
    conn = mysql_db.connection
    cur = conn.cursor()
    
    try: 
        conv_type = conversation_types[typeNum] # conv1, conv2, conv3 중 
        conv_id = request.json.get('conv_id')
        if conv_id == None:
            cur.execute(""" SELECT id FROM conversations WHERE user_id = %s AND chat_type = %s 
            ORDER BY id DESC LIMIT 1;""", (userid, conv_type))
            result = cur.fetchone()
            conv_id = result[0]

        cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s,%s, %s)",
                    (conv_id, 'bot', response))
        message_id = cur.lastrowid  # Get the ID of the newly inserted message
    except:
        return jsonify({'error': 404})
    finally:
        cur.close()
        conn.commit()

    return jsonify({'response': response, 'message_id': message_id, 'conv_id': conv_id})



@app.route('/api/chatReload/<int:typeNum>', methods=['POST'])
def chat_reload(typeNum):

    if typeNum not in [1, 2, 3]:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    userid = request.json.get('userid')

    chat_agents[userid][f'chat_agent{typeNum}'] = restart_agent(typeNum)

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


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)


