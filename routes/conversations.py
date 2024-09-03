from flask import Blueprint, jsonify
from __init__ import mysql_db
import MySQLdb.cursors

bp = Blueprint('conversations', __name__)

@bp.route('/get_conversations', methods=['GET'])
def get_conversations():
    cursor = mysql_db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM conversations')
    conversations = cursor.fetchall()
    cursor.close()
    return jsonify(conversations)
