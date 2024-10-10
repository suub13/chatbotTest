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



@app.route('/')
def main():
    email = session.get('email')  # 로그인된 사용자 이름을 세션에서 가져옴
    return render_template('main.html', email=email)  # 메인 페이지 렌더링 시 사용자 이름을 전달

conversation_types = {
    1: 'conv1ID',
    2: 'conv2ID',
    3: 'conv3ID'
}

@app.route('/api/botResponse/<int:chatbot_number>', methods=['POST'])
def bot_response(chatbot_number):
    # 로그인 되어 있는지 확인(되어있지 않으면 추후 자바스크립트에서 login 페이지로 redirect)
    if not session.get('email', False):
        return jsonify({'error': 'User not logged in'}), 401

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
    conn = mysql_db.connection
    cur = conn.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
    
    conv_type = conversation_types[chatbot_number]
    if conv_type not in session:
        user_id = session['user_id']
        cur.execute("INSERT INTO conversations (user_id, chat_type) VALUES (%s, %s)", (user_id, conv_type, ))
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
    global chat_agent1, chat_agent2, chat_agent3

    if chatbot_number not in [1, 2, 3]:
        return jsonify({'error': 'Invalid chatbot number'}), 400
    
    session.pop(conversation_types[chatbot_number], None)

    if chatbot_number == 1:
        chat_agent1 = restart_agent(chatbot_number)
    elif chatbot_number == 2:
        chat_agent2 = restart_agent(chatbot_number)
    elif chatbot_number == 3:
        chat_agent3 = restart_agent(chatbot_number)
    
    print(session)
    return '', 204

        
    

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        sex = request.form['sex']
        age = int(request.form['age'])
        email = request.form['email']
        print(name, password, sex, age, email)

        # 해시 알고리즘을 명확히 지정
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        conn = mysql_db.connection
        cur = conn.cursor()
        # try:
            # 사용자 이름과 이메일 중복 확인
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        print(f'existing user: {existing_user}')

        if existing_user:
            flash('입력하신 이메일이 이미 존재합니다. 중복 확인을 해주세요.')
            return render_template('login.html')

        # 중복이 없을 경우에만 사용자 추가
        cur.execute("INSERT INTO users (name, password, sex, age, email) VALUES (%s, %s, %s, %s, %s)",
                    (name, hashed_password, sex, age, email))

        conn.commit()
        cur.close()
        flash('회원가입을 환영합니다! 이제 로그인을 해주세요 ^^')
        session['show_login'] = True
        return redirect(url_for('login')+'?action=login')

    return render_template('login.html')

@app.route('/check_email')
def check_email():
    email = request.args.get('email')
    cur = mysql_db.connection.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        return {'exists': existing_user is not None}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cur.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login 들어옴")
    if request.method == 'POST':
        print("여기를 못들어와")
        email = request.form['email']
        password = request.form['password']
        print(email,password)

        cur = mysql_db.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE email = %s", [email])
            user = cur.fetchone()
            print(user)

            if user is None:
                flash('Email does not exist.', 'email_error')
                return redirect(url_for('login', action='login'))

            if check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['email'] = user[5]  
                print("통과")
                return redirect(url_for('main'))  # 메인 페이지로 리디렉션
            else:
                print("비밀번호 틀림")
                flash('Invalid password.', 'password_error')
                return redirect(url_for('login', action='login'))
        except Exception as e:
            flash('Database error: {}'.format(e))
            return render_template('login.html')
        finally:
            cur.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    print(f'로그아웃 후 {session}')
    # session.pop('name', None)  # 로그아웃 시 세션에서 사용자 이름 제거
    return redirect(url_for('main'))  # 메인 페이지로 리디렉션



@app.route('/reset_session', methods=['POST'])
def reset_session():
    session.clear()  # 세션을 초기화합니다.
    return '', 204  # No Content 응답



if __name__ == '__main__':
    chat_agent1 = restart_agent(1)
    chat_agent2 = restart_agent(2)
    chat_agent3 = restart_agent(3)
    
    app.run(debug=True)

