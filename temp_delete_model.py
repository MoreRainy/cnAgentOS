import sys
import os
import sqlite3
import json

# Define the absolute path to the database directly
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "app.db"))


def get_connection_direct():
    """A direct connection function using the absolute path."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def query_models():
    """
    Connects to the database and prints all entries from the model_engines table.
    """
    try:
        with get_connection_direct() as conn:
            rows = conn.execute(
                "SELECT * FROM model_engines ORDER BY created_at DESC"
            ).fetchall()

            print(f"--- Found {len(rows)} models in the database ---")
            if rows:
                for row in rows:
                    # Convert row to a dictionary and print as a JSON string
                    print(json.dumps(dict(row), indent=2))
            else:
                print("The model_engines table is empty.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    query_models()
