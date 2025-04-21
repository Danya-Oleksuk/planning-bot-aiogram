import datetime
import os
import uuid

import asyncpg
import pymongo
from dotenv import load_dotenv

from config import DB_CONFIG

load_dotenv()
pool = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)

async def create_telegram_channel_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                is_vip BOOLEAN DEFAULT FALSE,
                vip_until TIMESTAMP DEFAULT NULL,
                is_banned BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unique_key TEXT UNIQUE 
            ) 
        ''')

async def is_user_in_database(telegram_id: int) -> bool:
    async with pool.acquire() as conn:
        user_exists = await conn.fetchval('SELECT 1 FROM users WHERE telegram_id = $1', telegram_id)
        return bool(user_exists)

async def new_user_insert(user_id: int, first_name: str, last_name: str, username: str, is_vip: bool = False):
    unique_key = str(uuid.uuid4())

    async with pool.acquire() as conn:
        await conn.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, is_vip, joined_at, unique_key)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', user_id, first_name, last_name, username, is_vip, datetime.datetime.now(), unique_key)

async def get_user_is_banned(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT is_banned FROM users WHERE telegram_id = $1', user_id)
        return result

async def user_blocked_bot(user_id: int):
    async with pool.acquire() as conn:
        conn.execute('UPDATE users SET is_banned = TRUE WHERE telegram_id = $1', user_id)

async def user_unblocked_bot(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET is_banned = FALSE WHERE telegram_id = $1', user_id)

async def set_vip(user_id: int, until: datetime.datetime):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET is_vip = TRUE, vip_until = $1 WHERE telegram_id = $2', until, user_id)

async def set_vip_off(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET is_vip = FALSE, vip_until = NULL WHERE telegram_id = $1', user_id)

async def get_all_users_id():
    async with pool.acquire() as conn:
        data = await conn.fetch('SELECT telegram_id FROM users')
        return data

async def is_vip(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT is_vip FROM users WHERE telegram_id = $1', user_id)
        return result

async def get_all_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT telegram_id, first_name, username, joined_at FROM users')
        return result

async def get_vip_until(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT vip_until FROM users WHERE telegram_id = $1', user_id)
        return result

async def get_all_vip_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT telegram_id FROM users WHERE is_vip = TRUE')
        return result

async def get_all_not_vip_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT telegram_id FROM users WHERE is_vip = FALSE')
        return result

async def get_user_profile(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchrow('SELECT telegram_id, unique_key FROM users WHERE telegram_id = $1', user_id)
        return result


db = None
tasks_collection = None

async def create_mongo_database():
    global tasks_collection, db

    main_client = pymongo.AsyncMongoClient(os.environ.get('MONGO_API_TOKEN'))
    db = main_client['tasks_database']

    tasks_collection = db['tasks']

async def add_task(user_id: int, task_description: str):
    if tasks_collection is not None:
        task = {
            "user_id": user_id,
            "task": task_description,
            "status": "❌"
        }
        await tasks_collection.insert_one(task)

async def get_tasks(user_id: int):
    lst = []

    async for data in tasks_collection.find({"user_id": user_id}):
        lst.append({data.get("task"): data.get("status")})
    return lst

async def get_all_tasks():
    lst = []

    async for data in tasks_collection.find():
        lst.append(f"{data.get('user_id')} - {data.get('task')} - {data.get('status')}")
    return lst

async def count_tasks(user_id: int):
    return await tasks_collection.count_documents({"user_id": user_id})

async def get_status(user_id: int):
    data = await tasks_collection.find_one({"user_id": user_id})
    return data.get("status")

async def edit_task_status(user_id, task_number):
    if not await get_tasks(user_id):
        return False

    task_cursor = tasks_collection.find({"user_id": user_id}).sort([("_id", 1)])

    tasks_list = []
    async for task in task_cursor:
        tasks_list.append(task)

    if task_number > len(tasks_list):
        return False

    task_to_update = tasks_list[task_number - 1]

    await db.tasks.update_one(
        {"_id": task_to_update["_id"]},
        {"$set": {"status": "✅"}}
    )
    return True

async def delete_task(number_of_task: int, user_id: int):
    if not await get_tasks(user_id):
        return False

    tasks = tasks_collection.find({"user_id": user_id})
    tasks_list = [task async for task in tasks]

    if number_of_task - 1 < len(tasks_list):
        task_to_delete = tasks_list[number_of_task - 1]

        await tasks_collection.delete_one({"user_id": user_id, "task": task_to_delete.get("task"), "status": task_to_delete.get("status")})
        return True
    else:
        return False

async def delete_all_tasks(user_id: int):
    if not await get_tasks(user_id):
        return False

    await tasks_collection.delete_many({"user_id": user_id})
    return True