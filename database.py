import datetime
import sqlite3
import pymongo
from selenium.webdriver.common.devtools.v122.runtime import await_promise


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


db = None
tasks_collection = None

async def create_mongo_database():
    global tasks_collection, db

    main_client = pymongo.AsyncMongoClient("localhost", 27017)
    db = main_client['tasks_database']

    await db.drop_collection('tasks')  # !!! Dropping collection after each reload
    tasks_collection = db['tasks']

async def add_task(user_id: int, task_description: str):
    if tasks_collection is not None:
        task = {
            "user_id": user_id,
            "task": task_description,
            "status": "Не выполнено"
        }
        await tasks_collection.insert_one(task)

async def get_tasks(user_id: int):
    lst = []

    async for data in tasks_collection.find({"user_id": user_id}):
        lst.append({data.get("task"): data.get("status")})
    return lst

async def count_tasks(user_id: int):
    return await tasks_collection.count_documents({"user_id": user_id})

async def get_status(user_id: int, task_number: int):
    data = await tasks_collection.find_one({"user_id": user_id})
    return data.get("status")

async def edit_task_status(user_id, task_number):  #Status
    if not await get_tasks(user_id):
        return False

    task_cursor = tasks_collection.find({"user_id": user_id})

    tasks_list = []
    async for task in task_cursor:
        tasks_list.append(task)

    task_to_update = tasks_list[task_number - 1]
    await db.tasks.update_one({"user_id": user_id, "task": task_to_update.get("task")}, {"$set": {"status": "Выполнено"}})
    return True

async def delete_task(number_of_task: int, user_id: int):
    if not await get_tasks(user_id):
        return False

    tasks = tasks_collection.find({"user_id": user_id})
    tasks_list = [task async for task in tasks]

    if number_of_task - 1 < len(tasks_list):
        task_to_delete = tasks_list[number_of_task - 1]

        res = await tasks_collection.delete_one(
            {"user_id": user_id, "task": task_to_delete.get("task"), "status": task_to_delete.get("status")})
        return True

    else:
        return False

async def delete_all_tasks(user_id: int):
    if not await get_tasks(user_id):
        return False

    await tasks_collection.delete_many({"user_id": user_id})
    return True