import datetime
import sqlite3
import pymongo


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


tasks_collection = None

async def create_mongo_database():
    global tasks_collection

    main_client = pymongo.AsyncMongoClient("localhost", 27017)
    db = main_client['tasks_database']

    await db.drop_collection('tasks') # !!! Dropping collection after each reload
    tasks_collection = db['tasks']

async def add_task(user_id: int, task_description: str):
    if tasks_collection is not None:
        task = {
            "user_id": user_id,
            "task": task_description,
            "status": "⏳Не выполнено"
        }
        await tasks_collection.insert_one(task)

async def get_tasks(user_id: int):

    lst = []
    async for data in tasks_collection.find():
        lst.append(data.get("task"))
    return lst

async def edit_task(): #Topic
    pass

async def update_task(): #Status
    pass

async def delete_task():
    pass

async def delete_all_tasks(user_id: int):
    if not await get_tasks(user_id):
        return False
    await tasks_collection.delete_many({"user_id": user_id})
    return True