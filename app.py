
import os
import logging

import pymysql
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "todo_user"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "todo_db"),
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 5
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)
        connection.commit()
        logging.info("Database initialized")
    finally:
        connection.close()


@app.route("/")
def index():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
            tasks = cursor.fetchall()
    finally:
        connection.close()

    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()

    if title:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO tasks (title) VALUES (%s)",
                    (title,)
                )
            connection.commit()
            logging.info("Task added")
        finally:
            connection.close()

    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE tasks SET completed = TRUE WHERE id = %s",
                (task_id,)
            )
        connection.commit()
        logging.info("Task %s completed", task_id)
    finally:
        connection.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,)
            )
        connection.commit()
        logging.info("Task %s deleted", task_id)
    finally:
        connection.close()

    return redirect(url_for("index"))


@app.route("/health")
def health():
    try:
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        finally:
            connection.close()
        return {"status": "ok"}, 200
    except pymysql.MySQLError:
        logging.exception("Database health check failed")
        return {"status": "error"}, 503


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
