from __future__ import annotations

import asyncio
from typing import List, Optional, Type

import aiosqlite
import argon2
from pydantic import SecretStr


class Database:
    def __init__(self):
        self.conn: Optional[aiosqlite.Connection] = None
        self.write_lock = asyncio.Lock()
        self.ph = argon2.PasswordHasher()

    async def setup_db_if_not_already(self):
        assert self.conn is not None
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS user_auth (
                    uname TEXT PRIMARY KEY,
                    name TEXT,
                    pass TEXT
                )"""
            )

    async def connect(self, path: str = "data/database.db"):
        self.conn = aiosqlite.connect(path)
        await self.conn

    async def close(self):
        assert self.conn is not None
        await self.conn.close()
        self.conn = None

    # read operations
    async def list_users(self) -> List[str]:
        assert self.conn is not None
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT name FROM user_auth")
            rows = await cursor.fetchall()
        return [user_name for user_name, in rows]

    async def find_user_name(self, name: str) -> bool:
        assert self.conn is not None

        uname = name.lower()
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT name FROM user_auth WHERE uname=?", (uname,))
            row = await cursor.fetchone()
        return row is not None and name == row[0]

    async def check_user(self, name: str, password: SecretStr) -> Optional[str]:
        assert self.conn is not None

        uname = name.lower()
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT name, pass FROM user_auth WHERE uname=?", (uname,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        db_name, db_hashed_password = row
        if name != db_name:
            return None
        try:
            self.ph.verify(db_hashed_password, password.get_secret_value())
            return uname
        except argon2.exceptions.VerifyMismatchError:
            return None

    # write operations
    async def register_user(self, name: str, password: SecretStr):
        assert self.conn is not None
        uname = name.lower()
        hashed_password = self.ph.hash(password.get_secret_value())
        async with self.write_lock:
            async with self.conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO user_auth (uname, name, pass) VALUES (?, ?, ?)",
                    (uname, name, hashed_password),
                )
                await self.conn.commit()

    async def reset_password(self, name: str, password: SecretStr):
        assert self.conn is not None
        uname = name.lower()
        hashed_password = self.ph.hash(password.get_secret_value())
        async with self.write_lock:
            async with self.conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE user_auth SET pass=? WHERE uname=?",
                    (hashed_password, uname),
                )
                await self.conn.commit()

    async def delete_user(self, name: str) -> bool:
        assert self.conn is not None
        uname = name.lower()
        async with self.write_lock:
            async with self.conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM user_auth WHERE uname=?",
                    (uname,),
                )
                affected_rows = cursor.rowcount
                await self.conn.commit()
        assert affected_rows == 0 or affected_rows == 1
        return affected_rows > 0

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Type[BaseException]],
    ):
        await self.close()
