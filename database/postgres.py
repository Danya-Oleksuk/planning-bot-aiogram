import datetime
import uuid

import asyncpg

from config import DB_CONFIG


async def initiate_pool():
    pool = await asyncpg.create_pool(**DB_CONFIG)
    return pool


async def create_telegram_bot_db():
    conn = await asyncpg.connect(**DB_CONFIG)

    await conn.execute(
        """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unique_key TEXT UNIQUE 
            ) 
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bans (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                is_banned_by_admin BOOLEAN DEFAULT FALSE,
                is_banned_by_self BOOLEAN DEFAULT FALSE,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vip_status (
            user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
            is_vip BOOLEAN DEFAULT FALSE,
            vip_until TIMESTAMP DEFAULT NULL,
            PRIMARY KEY (user_id)
        )
    """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_stats (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE REFERENCES users(telegram_id) ON DELETE CASCADE,
            total_tasks INTEGER DEFAULT 0,
            completed_tasks INTEGER DEFAULT 0
        )
    """
    )
    await conn.close()


class UserRepository:
    def __init__(self, db_pool):
        self.pool = db_pool

    async def is_user_in_database(self, telegram_id: int) -> bool:
        async with self.pool.acquire() as conn:
            user_exists = await conn.fetchval(
                "SELECT 1 FROM users WHERE telegram_id = $1", telegram_id
            )
            return bool(user_exists)

    async def create_user(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        username: str,
        is_vip: bool = False,
    ):
        unique_key = str(uuid.uuid4())

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                        INSERT INTO users (telegram_id, first_name, last_name, username, joined_at, unique_key)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id,
                    first_name,
                    last_name,
                    username,
                    datetime.datetime.now(),
                    unique_key,
                )

            await conn.execute(
                """
                INSERT INTO bans (user_id) VALUES ($1)
            """,
                user_id,
            )

            await conn.execute(
                """
                INSERT INTO vip_status (user_id, is_vip, vip_until)
                VALUES ($1, $2, $3)
            """,
                user_id,
                is_vip,
                None,
            )

    async def user_blocked_bot(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE bans SET is_banned_by_self = TRUE WHERE user_id = $1",
                    user_id,
                )

    async def user_unblocked_bot(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE bans SET is_banned_by_self = FALSE WHERE user_id = $1",
                    user_id,
                )

    async def block_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE bans SET is_banned_by_admin = TRUE WHERE user_id = $1",
                    user_id,
                )
                return True

    async def unblock_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE bans SET is_banned_by_admin = FALSE WHERE user_id = $1",
                    user_id,
                )
                return True

    async def get_user_is_banned_by_admin(self, user_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_banned_by_admin FROM bans WHERE user_id = $1", user_id
            )
            return result

    async def get_user_is_banned(self, user_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_banned_by_self FROM bans WHERE user_id = $1", user_id
            )
            return result

    async def get_user_profile(self, user_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT telegram_id, unique_key FROM users WHERE telegram_id = $1",
                user_id,
            )
            return result

    async def get_all_users_id(self):
        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT telegram_id FROM users")
            return [record["telegram_id"] for record in records]

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            result = await conn.fetch(
                """
                    SELECT u.telegram_id, u.first_name, u.username, u.joined_at, b.is_banned_by_self
                    FROM users u
                    JOIN bans b ON u.telegram_id = b.user_id
                """
            )
            return result


class VipRepository:
    def __init__(self, db_pool):
        self.pool = db_pool

    async def activate_vip(self, user_id: int, until: datetime.datetime):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE vip_status SET is_vip = TRUE, vip_until = $1 WHERE user_id = $2",
                    until,
                    user_id,
                )

    async def deactivate_vip(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE vip_status SET is_vip = FALSE, vip_until = NULL WHERE user_id = $1",
                    user_id,
                )

    async def is_user_vip(self, user_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_vip FROM vip_status WHERE user_id = $1", user_id
            )
            return result

    async def get_vip_expiration(self, user_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT vip_until FROM vip_status WHERE user_id = $1", user_id
            )
            return result

    async def get_all_vip_users(self):
        async with self.pool.acquire() as conn:
            result = await conn.fetch(
                "SELECT user_id FROM vip_status WHERE is_vip = TRUE"
            )
            return result

    async def get_all_not_vip_users(self):
        async with self.pool.acquire() as conn:
            result = await conn.fetch(
                "SELECT user_id FROM vip_status WHERE is_vip = FALSE"
            )
            return result


class StatsRepository:
    def __init__(self, db_pool):
        self.pool = db_pool

    async def get_user_stats(self, user_id: int):
        async with self.pool.acquire() as conn:
            user_stats = await conn.fetchrow(
                "SELECT total_tasks, completed_tasks FROM user_stats WHERE user_id = $1",
                user_id,
            )
            return dict(user_stats) if user_stats else None

    async def increment_total_tasks(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                exists = await conn.fetchval(
                    "SELECT 1 FROM user_stats WHERE user_id = $1", user_id
                )

                if not exists:
                    await conn.execute(
                        "INSERT INTO user_stats(user_id, total_tasks) VALUES($1, 1)",
                        user_id,
                    )
                else:
                    await conn.execute(
                        "UPDATE user_stats SET total_tasks = total_tasks + 1 WHERE user_id = $1",
                        user_id,
                    )

    async def increment_completed_tasks(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                exists = await conn.fetchval(
                    "SELECT 1 FROM user_stats WHERE user_id = $1", user_id
                )

                if not exists:
                    await conn.execute(
                        "INSERT INTO user_stats(user_id, completed_tasks) VALUES($1, 1)",
                        user_id,
                    )
                else:
                    await conn.execute(
                        "UPDATE user_stats SET completed_tasks = completed_tasks + 1 WHERE user_id = $1",
                        user_id,
                    )
