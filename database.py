import datetime
import sqlite3

def create_telegram_channel_db():
  conn = sqlite3.connect('users_data_base.db')
  cursor = conn.cursor()

  cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          telegram_id INTEGER UNIQUE,
          first_name TEXT,
          last_name TEXT,
          joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
  conn.commit()
  conn.close()

def is_user_in_database(telegram_id: int):
  conn = sqlite3.connect('users_data_base.db')
  cursor = conn.cursor()

  cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
  result = cursor.fetchone()

  conn.close()

  return result is not None

def new_user_insert(user_id: int, first_name: str, last_name: str):
    db_name = 'users_data_base.db'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
            INSERT INTO users (telegram_id, first_name, last_name, joined_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, first_name, last_name, datetime.datetime.now()))

    conn.commit()
    conn.close()
