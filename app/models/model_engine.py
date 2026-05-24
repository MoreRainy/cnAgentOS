from __future__ import annotations

from typing import Any

from .db import get_connection


class ModelEngineRepository:
    @staticmethod
    def create_model(
        name: str,
        model_name: str,
        base_url: str,
        api_key: str,
        is_default: int = 0,
    ) -> int:
        with get_connection() as conn:
            if is_default:
                conn.execute("UPDATE model_engines SET is_default = 0")

            cursor = conn.execute(
                """
                INSERT INTO model_engines (name, model_name, base_url, api_key, is_default)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, model_name, base_url, api_key, int(is_default)),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def get_all_models(page: int = 1, per_page: int = 6) -> tuple[list[Any], int]:
        offset = (page - 1) * per_page
        with get_connection() as conn:
            models = conn.execute(
                """
                SELECT id, name, model_name, api_key, base_url, is_default, token_count, created_at
                FROM model_engines
                ORDER BY is_default DESC, created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM model_engines").fetchone()[0]
        return models, int(total)

    @staticmethod
    def get_model_by_id(model_id: int):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT id, name, model_name, api_key, base_url, is_default, token_count, created_at
                FROM model_engines
                WHERE id = ?
                """,
                (model_id,),
            ).fetchone()

    @staticmethod
    def update_model(
        model_id: int,
        name: str,
        model_name: str,
        api_key: str,
        base_url: str,
        is_default: int = 0,
    ) -> bool:
        with get_connection() as conn:
            current = conn.execute(
                "SELECT id FROM model_engines WHERE id = ?",
                (model_id,),
            ).fetchone()
            if not current:
                return False

            if is_default:
                conn.execute("UPDATE model_engines SET is_default = 0 WHERE id <> ?", (model_id,))

            conn.execute(
                """
                UPDATE model_engines
                SET name = ?, model_name = ?, api_key = ?, base_url = ?, is_default = ?
                WHERE id = ?
                """,
                (name, model_name, api_key, base_url, int(is_default), model_id),
            )
            return True

    @staticmethod
    def delete_model(model_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("DELETE FROM model_engines WHERE id = ?", (model_id,))
            return True

    @staticmethod
    def set_default_model(model_id: int) -> bool:
        with get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM model_engines WHERE id = ?",
                (model_id,),
            ).fetchone()
            if not exists:
                return False
            conn.execute("UPDATE model_engines SET is_default = 0")
            conn.execute("UPDATE model_engines SET is_default = 1 WHERE id = ?", (model_id,))
            return True

    @staticmethod
    def get_default_model():
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT id, name, model_name, api_key, base_url, is_default, token_count, created_at
                FROM model_engines
                WHERE is_default = 1
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

    @staticmethod
    def increment_token_count(model_id: int, count: int) -> bool:
        with get_connection() as conn:
            conn.execute(
                "UPDATE model_engines SET token_count = COALESCE(token_count, 0) + ? WHERE id = ?",
                (int(count), model_id),
            )
            return True
