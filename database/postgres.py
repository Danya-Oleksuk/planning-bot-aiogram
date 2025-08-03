import asyncpg
import uuid
import datetime

from config import DB_CONFIG


pool = None

async def initiate_pool():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)

async def create_telegram_bot_db():
    conn = await asyncpg.connect(**DB_CONFIG)

    await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unique_key TEXT UNIQUE 
            ) 
        ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS vip_status (
            user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
            is_vip BOOLEAN DEFAULT FALSE,
            vip_until TIMESTAMP DEFAULT NULL,
            PRIMARY KEY (user_id)
        )
    ''')

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE REFERENCES users(telegram_id) ON DELETE CASCADE,
            total_tasks INTEGER DEFAULT 0,
            completed_tasks INTEGER DEFAULT 0
        )
    ''')
    await conn.close()

async def is_user_in_database(telegram_id: int) -> bool:
    async with pool.acquire() as conn:
        user_exists = await conn.fetchval('SELECT 1 FROM users WHERE telegram_id = $1', telegram_id)
        return bool(user_exists)

async def create_user(user_id: int, first_name: str, last_name: str, username: str, is_vip: bool = False):
    unique_key = str(uuid.uuid4())

    async with pool.acquire() as conn:
        await conn.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, joined_at, unique_key)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', user_id, first_name, last_name, username, datetime.datetime.now(), unique_key)
        

        await conn.execute('''
            INSERT INTO vip_status (user_id, is_vip, vip_until)
            VALUES ($1, $2, $3)
        ''', user_id, is_vip, None)

async def get_user_stats(user_id: int):
    async with pool.acquire() as conn:
        user_stats = await conn.fetchrow('SELECT total_tasks, completed_tasks FROM user_stats WHERE user_id = $1', user_id)
        return dict(user_stats) if user_stats else None

async def increment_total_tasks(user_id: int):
    async with pool.acquire() as conn:
        exists = await conn.fetchval('SELECT 1 FROM user_stats WHERE user_id = $1', user_id)
        
        if not exists:
            await conn.execute('INSERT INTO user_stats(user_id, total_tasks) VALUES($1, 1)', user_id)
        else:
            await conn.execute('UPDATE user_stats SET total_tasks = total_tasks + 1 WHERE user_id = $1', user_id)

async def increment_completed_tasks(user_id: int):
    async with pool.acquire() as conn:
        exists = await conn.fetchval('SELECT 1 FROM user_stats WHERE user_id = $1', user_id)

        if not exists:
            await conn.execute('INSERT INTO user_stats(user_id, completed_tasks) VALUES($1, 1)', user_id)
        else:
            await conn.execute('UPDATE user_stats SET completed_tasks = completed_tasks + 1 WHERE user_id = $1', user_id)
                    
async def user_blocked_bot(user_id: int):
    async with pool.acquire() as conn:
        conn.execute('UPDATE users SET is_banned = TRUE WHERE telegram_id = $1', user_id)

async def user_unblocked_bot(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET is_banned = FALSE WHERE telegram_id = $1', user_id)

async def activate_vip(user_id: int, until: datetime.datetime):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE vip_status SET is_vip = TRUE, vip_until = $1 WHERE user_id = $2', until, user_id)

async def deactivate_vip(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute('UPDATE vip_status SET is_vip = FALSE, vip_until = NULL WHERE user_id = $1', user_id)

async def get_user_is_banned(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT is_banned FROM users WHERE telegram_id = $1', user_id)
        return result
    
async def is_user_vip(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT is_vip FROM vip_status WHERE user_id = $1', user_id)
        return result
    
async def get_vip_expiration(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT vip_until FROM vip_status WHERE user_id = $1', user_id)
        return result
    
async def get_user_profile(user_id: int):
    async with pool.acquire() as conn:
        result = await conn.fetchrow('SELECT telegram_id, unique_key FROM users WHERE telegram_id = $1', user_id)
        return result
    
async def get_all_users_id():
    async with pool.acquire() as conn:
        records = await conn.fetch('SELECT telegram_id FROM users')
        return [record['telegram_id'] for record in records]

async def get_all_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT telegram_id, first_name, username, joined_at FROM users')
        return result

async def get_all_vip_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT user_id FROM vip_status WHERE is_vip = TRUE')
        return result

async def get_all_not_vip_users():
    async with pool.acquire() as conn:
        result = await conn.fetch('SELECT user_id FROM vip_status WHERE is_vip = FALSE')
        return result