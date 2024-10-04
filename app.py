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
        password=app.config['MYSQL_PASSWORD']
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


# 애플리케이션 시작 시 SQL 스크립트 실행
run_sql_script('setup.sql')

chat_agent1 = None
chat_agent2 = None
chat_agent3 = None


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
    username = session.get('username')  # 로그인된 사용자 이름을 세션에서 가져옴
    return render_template('main.html', username=username)  # 메인 페이지 렌더링 시 사용자 이름을 전달

chat_agents = {
    1: chat_agent1,
    2: chat_agent2,
    3: chat_agent3 
}

@app.route('/api/botResponse/<int:chatbot_number>', methods=['POST'])
def bot_response(chatbot_number):
    data = request.json
    user_message = data.get('message')

    # 적절한 챗봇 에이전트를 선택
    chat_agent = chat_agents[chatbot_number]
    if not chat_agent:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    response = chat_agent.invoke_agent(user_message)
    cur = mysql_db.connection.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
    
    conversation_types = {
        1: 'conv1',
        2: 'conv2',
        3: 'conv3'
    }

    conv_type = conversation_types[chatbot_number]
        
    if conv_type not in session:
        user_id = session['user_id']
        cur.execute("INSERT INTO conversations (user_id, chat_type) VALUES (%s, %s)",
                    (user_id, conv_type))
        conversation_id = cur.lastrowid
        session[conv_type] = conversation_id
        
    else:
        conversation_id = session[conv_type]

        cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s, %s)",
                    (conversation_id, 'user', user_message))
        cur.execute("INSERT INTO messages (conversation_id, sender, content) VALUES (%s, %s)",
                    (conversation_id, 'bot', response))

    return jsonify({'response': response})

@app.route('/api/chatReload/<int:chatbot_number>', methods=['GET'])
def chat_reload(chatbot_number):
    if chatbot_number in chat_agents:
        chat_agents[chatbot_number] = restart_agent(chatbot_number)
        return jsonify({'message': f'New agent instance created for chatbot {chatbot_number}'})
    else:
        return jsonify({'error': 'Invalid chatbot number'}), 400



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        sex = request.form['sex']
        age = int(request.form['age'])
        email = request.form['email']

        # 해시 알고리즘을 명확히 지정
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cur = mysql_db.connection.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.')
            return render_template('register.html')

        # 중복이 없을 경우에만 사용자 추가
        cur.execute("INSERT INTO users (name, username, password, sex, age, email) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, username, hashed_password, sex, age, email))
        mysql_db.connection.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
        # except Exception as e:
        #     flash(f'An error occurred: {e}')
        #     return render_template('register.html')
        # finally:
            # cur.close()
    return render_template('register.html')

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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)

        cur = mysql_db.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cur.fetchone()
            print(f'{user}없음?')
            if user is None:
                return render_template('login.html', username_error='Username does not exist.')

            if check_password_hash(user[3], password):
                session['username'] = user[2]  # 로그인 성공 시 세션에 사용자 이름 저장
                # session['chat_agent1'] = restart_agent(1)
                # session['chat_agent2'] = restart_agent(2)
                # session['chat_agent3'] = restart_agent(3)

                session['user_id'] = user[0]
                return redirect(url_for('main'))  # 메인 페이지로 리디렉션
            else:
                return render_template('login.html', password_error='Invalid password.')
        except Exception as e:
            print("이거야?")
            flash('Database error: {}'.format(e))
            return render_template('login.html')
        finally:
            cur.close()
    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        return f"Hello, {session['username']}!"
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)  # 로그아웃 시 세션에서 사용자 이름 제거
    return redirect(url_for('main'))  # 메인 페이지로 리디렉션


# @app.route('/reset_session', methods=['POST'])
# def reset_session():
#     session.clear()  # 세션을 초기화합니다.
#     return '', 204  # No Content 응답


if __name__ == '__main__':
    chat_agent1 = restart_agent(1)
    chat_agent2 = restart_agent(2)
    chat_agent3 = restart_agent(3)

    app.run(debug=True)