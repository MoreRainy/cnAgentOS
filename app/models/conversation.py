import sqlite3
from typing import List, Optional, Tuple

from app.models.db import get_connection


class ConversationRepository:
    @staticmethod
    def create_conversation(user_id: int, title: str = "新对话") -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "insert into conversations (user_id, title) values (?, ?)",
                (user_id, title),
            )
            return cursor.lastrowid

    @staticmethod
    def get_conversations_by_user(user_id: int) -> list:
        with get_connection() as conn:
            return conn.execute(
                "select id, user_id, title, created_at, updated_at from conversations "
                "where user_id=? order by updated_at desc",
                (user_id,),
            ).fetchall()

    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            return conn.execute(
                "select id, user_id, title, created_at, updated_at from conversations where id=?",
                (conversation_id,),
            ).fetchone()

    @staticmethod
    def update_conversation_title(conversation_id: int, title: str) -> bool:
        with get_connection() as conn:
            conn.execute(
                "update conversations set title=?, updated_at=datetime('now','localtime') where id=?",
                (title, conversation_id),
            )
            return True

    @staticmethod
    def delete_conversation(conversation_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            conn.execute(
                "delete from messages where conversation_id=?", (conversation_id,)
            )
            conn.execute(
                "delete from conversations where id=? and user_id=?",
                (conversation_id, user_id),
            )
            return True


class MessageRepository:
    @staticmethod
    def add_message(conversation_id: int, role: str, content: str) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "insert into messages (conversation_id, role, content) values (?, ?, ?)",
                (conversation_id, role, content),
            )
            conn.execute(
                "update conversations set updated_at=datetime('now','localtime') where id=?",
                (conversation_id,),
            )
            return cursor.lastrowid

    @staticmethod
    def get_messages_by_conversation(conversation_id: int) -> list:
        with get_connection() as conn:
            return conn.execute(
                "select id, conversation_id, role, content, created_at from messages "
                "where conversation_id=? order by created_at asc",
                (conversation_id,),
            ).fetchall()

    @staticmethod
    def get_last_message(conversation_id: int) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            return conn.execute(
                "select id, conversation_id, role, content, created_at from messages "
                "where conversation_id=? order by created_at desc limit 1",
                (conversation_id,),
            ).fetchone()
