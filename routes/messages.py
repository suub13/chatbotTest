from flask import Blueprint, request, jsonify
from __init__ import mysql_db
import MySQLdb.cursors

bp = Blueprint('messages', __name__)

@bp.route('/message', methods=['POST'])
def message():
    data = request.get_json()
    history = data['history']
    conversation_id = data.get('conversation_id')

    cursor = mysql_db.connection.cursor(MySQLdb.cursors.DictCursor)
    if not conversation_id:
        cursor.execute('INSERT INTO conversations () VALUES ()')
        conversation_id = cursor.lastrowid
        mysql_db.connection.commit()

    for msg in history:
        cursor.execute('INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)', (conversation_id, msg['sender'], msg['text']))
    mysql_db.connection.commit()

    bot_response = '챗봇의 응답입니다.'
    cursor.execute('INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)', (conversation_id, 'bot', bot_response))
    mysql_db.connection.commit()

    cursor.close()
    return jsonify({'response': bot_response, 'conversation_id': conversation_id})

@bp.route('/get_messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    cursor = mysql_db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM messages WHERE conversation_id = %s', (conversation_id,))
    messages = cursor.fetchall()
    cursor.close()
    return jsonify(messages)
