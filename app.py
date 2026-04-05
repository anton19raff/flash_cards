"""Educational Flask app for learning greeting words in 50 languages."""
from __future__ import annotations

import os
import random
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "greetings.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-me"


SEED_GREETINGS: list[tuple[str, str, str, str]] = [
    ("English", "Hello", "Привет", "Universal informal greeting"),
    ("Spanish", "Hola", "Привет", "Common friendly greeting"),
    ("French", "Bonjour", "Добрый день", "Formal daytime greeting"),
    ("German", "Hallo", "Привет", "Neutral greeting"),
    ("Italian", "Ciao", "Привет/Пока", "Informal hello and bye"),
    ("Portuguese", "Olá", "Привет", "Used in Brazil and Portugal"),
    ("Dutch", "Hallo", "Привет", "Basic greeting"),
    ("Swedish", "Hej", "Привет", "Very common casual greeting"),
    ("Norwegian", "Hei", "Привет", "Standard casual greeting"),
    ("Danish", "Hej", "Привет", "Common informal greeting"),
    ("Finnish", "Hei", "Привет", "Standard hello"),
    ("Polish", "Cześć", "Привет", "Informal greeting"),
    ("Czech", "Ahoj", "Привет", "Informal hello"),
    ("Slovak", "Ahoj", "Привет", "Casual greeting"),
    ("Hungarian", "Szia", "Привет", "Informal greeting"),
    ("Romanian", "Salut", "Привет", "Common friendly greeting"),
    ("Greek", "Γειά σου", "Привет", "Informal singular greeting"),
    ("Turkish", "Merhaba", "Здравствуйте", "Neutral polite greeting"),
    ("Arabic", "مرحبا", "Привет", "General greeting"),
    ("Hebrew", "שלום", "Привет/Мир", "Hello and peace"),
    ("Persian", "سلام", "Привет", "Common greeting"),
    ("Hindi", "नमस्ते", "Здравствуйте", "Respectful greeting"),
    ("Urdu", "السلام علیکم", "Мир вам", "Formal Islamic greeting"),
    ("Bengali", "হ্যালো", "Привет", "Modern colloquial greeting"),
    ("Punjabi", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "Здравствуйте", "Traditional Sikh greeting"),
    ("Tamil", "வணக்கம்", "Здравствуйте", "Respectful greeting"),
    ("Telugu", "నమస్కారం", "Здравствуйте", "Formal greeting"),
    ("Marathi", "नमस्कार", "Здравствуйте", "Polite greeting"),
    ("Gujarati", "નમસ્તે", "Здравствуйте", "Respectful greeting"),
    ("Chinese (Mandarin)", "你好", "Привет", "Most common greeting"),
    ("Japanese", "こんにちは", "Добрый день", "Daytime greeting"),
    ("Korean", "안녕하세요", "Здравствуйте", "Polite hello"),
    ("Vietnamese", "Xin chào", "Здравствуйте", "Neutral greeting"),
    ("Thai", "สวัสดี", "Здравствуйте", "Polite greeting"),
    ("Indonesian", "Halo", "Привет", "Casual greeting"),
    ("Malay", "Hai", "Привет", "Informal greeting"),
    ("Filipino", "Kamusta", "Как дела", "Common Filipino greeting"),
    ("Swahili", "Jambo", "Привет", "Tourist-friendly greeting"),
    ("Zulu", "Sawubona", "Здравствуйте", "Singular greeting"),
    ("Xhosa", "Molo", "Привет", "Common greeting"),
    ("Afrikaans", "Hallo", "Привет", "Standard greeting"),
    ("Amharic", "ሰላም", "Привет", "General greeting"),
    ("Yoruba", "Bawo", "Как дела", "Informal greeting"),
    ("Igbo", "Ndewo", "Здравствуйте", "Polite greeting"),
    ("Hausa", "Sannu", "Здравствуйте", "General greeting"),
    ("Ukrainian", "Привіт", "Привет", "Informal greeting"),
    ("Belarusian", "Вітаю", "Приветствую", "Polite greeting"),
    ("Serbian", "Здраво", "Привет", "Neutral greeting"),
    ("Croatian", "Bok", "Привет", "Informal greeting"),
    ("Lithuanian", "Labas", "Привет", "Casual greeting"),
]


def get_db() -> sqlite3.Connection:
    """Return db connection attached to app context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    """Close db on request teardown."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Initialize database schema and seed data."""
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS greetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL UNIQUE,
            greeting TEXT NOT NULL,
            translation_ru TEXT NOT NULL,
            note TEXT NOT NULL
        )
        """
    )
    count = db.execute("SELECT COUNT(*) AS c FROM greetings").fetchone()[0]
    if count == 0:
        db.executemany(
            """
            INSERT INTO greetings (language, greeting, translation_ru, note)
            VALUES (?, ?, ?, ?)
            """,
            SEED_GREETINGS,
        )
    db.commit()
    db.close()


def validate_greeting_form(form: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """Validate add/edit form and return cleaned data + errors."""
    cleaned = {
        "language": form.get("language", "").strip(),
        "greeting": form.get("greeting", "").strip(),
        "translation_ru": form.get("translation_ru", "").strip(),
        "note": form.get("note", "").strip(),
    }
    errors: dict[str, str] = {}

    if len(cleaned["language"]) < 2:
        errors["language"] = "Язык должен содержать минимум 2 символа."
    if len(cleaned["greeting"]) < 1:
        errors["greeting"] = "Введите слово приветствия."
    if len(cleaned["translation_ru"]) < 2:
        errors["translation_ru"] = "Добавьте перевод на русский язык."
    if len(cleaned["note"]) < 5:
        errors["note"] = "Комментарий должен быть не короче 5 символов."

    return cleaned, errors


@app.route("/")
def home() -> str:
    """Render landing page with project description."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS c FROM greetings").fetchone()["c"]
    return render_template("home.html", total=total)


@app.route("/greetings")
def greetings_list() -> str:
    """Render full list of greeting cards."""
    db = get_db()
    query = request.args.get("q", "").strip()
    if query:
        cards = db.execute(
            """
            SELECT * FROM greetings
            WHERE lower(language) LIKE lower(?) OR lower(greeting) LIKE lower(?)
            ORDER BY language
            """,
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        cards = db.execute("SELECT * FROM greetings ORDER BY language").fetchall()
    return render_template("greetings.html", cards=cards, query=query)


@app.route("/greetings/<int:card_id>")
def greeting_detail(card_id: int) -> str:
    """Render card detail page."""
    db = get_db()
    card = db.execute("SELECT * FROM greetings WHERE id = ?", (card_id,)).fetchone()
    if card is None:
        return render_template("not_found.html"), 404
    return render_template("greeting_detail.html", card=card)


@app.route("/greetings/add", methods=["GET", "POST"])
def greeting_add() -> str:
    """Add greeting card via validated form."""
    values: dict[str, str] = {
        "language": "",
        "greeting": "",
        "translation_ru": "",
        "note": "",
    }
    errors: dict[str, str] = {}

    if request.method == "POST":
        values, errors = validate_greeting_form(request.form)
        if not errors:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM greetings WHERE lower(language)=lower(?)",
                (values["language"],),
            ).fetchone()
            if exists:
                errors["language"] = "Карточка с таким языком уже существует."
            else:
                db.execute(
                    """
                    INSERT INTO greetings (language, greeting, translation_ru, note)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        values["language"],
                        values["greeting"],
                        values["translation_ru"],
                        values["note"],
                    ),
                )
                db.commit()
                flash("Новая карточка успешно добавлена.", "success")
                return redirect(url_for("greetings_list"))

    return render_template("greeting_form.html", values=values, errors=errors, mode="add")


@app.route("/greetings/<int:card_id>/edit", methods=["GET", "POST"])
def greeting_edit(card_id: int) -> str:
    """Edit greeting card via validated form."""
    db = get_db()
    card = db.execute("SELECT * FROM greetings WHERE id = ?", (card_id,)).fetchone()
    if card is None:
        return render_template("not_found.html"), 404

    values = {
        "language": card["language"],
        "greeting": card["greeting"],
        "translation_ru": card["translation_ru"],
        "note": card["note"],
    }
    errors: dict[str, str] = {}

    if request.method == "POST":
        values, errors = validate_greeting_form(request.form)
        if not errors:
            exists = db.execute(
                "SELECT id FROM greetings WHERE lower(language)=lower(?) AND id != ?",
                (values["language"], card_id),
            ).fetchone()
            if exists:
                errors["language"] = "Другой карточке уже назначен этот язык."
            else:
                db.execute(
                    """
                    UPDATE greetings
                    SET language = ?, greeting = ?, translation_ru = ?, note = ?
                    WHERE id = ?
                    """,
                    (
                        values["language"],
                        values["greeting"],
                        values["translation_ru"],
                        values["note"],
                        card_id,
                    ),
                )
                db.commit()
                flash("Карточка обновлена.", "success")
                return redirect(url_for("greeting_detail", card_id=card_id))

    return render_template("greeting_form.html", values=values, errors=errors, mode="edit", card_id=card_id)


@app.route("/greetings/<int:card_id>/delete", methods=["POST"])
def greeting_delete(card_id: int) -> Any:
    """Delete greeting card by id."""
    db = get_db()
    db.execute("DELETE FROM greetings WHERE id = ?", (card_id,))
    db.commit()
    flash("Карточка удалена.", "success")
    return redirect(url_for("greetings_list"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz() -> str:
    """Simple quiz where user matches language to greeting."""
    db = get_db()
    cards = db.execute("SELECT * FROM greetings ORDER BY RANDOM() LIMIT 4").fetchall()
    correct_card = random.choice(cards)

    message = ""
    message_type = ""
    selected = ""
    if request.method == "POST":
        selected = request.form.get("answer", "")
        correct = request.form.get("correct", "")
        if selected == "":
            message = "Выберите вариант ответа перед проверкой."
            message_type = "error"
        elif selected == correct:
            message = "Верно! Отличная работа."
            message_type = "success"
        else:
            message = "Пока неверно. Попробуйте следующий вопрос."
            message_type = "error"

    return render_template(
        "quiz.html",
        cards=cards,
        correct_card=correct_card,
        message=message,
        message_type=message_type,
        selected=selected,
    )


@app.route("/stats")
def stats() -> str:
    """Show simple statistics page."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS c FROM greetings").fetchone()["c"]
    examples = db.execute("SELECT language, greeting FROM greetings ORDER BY language LIMIT 10").fetchall()
    return render_template("stats.html", total=total, examples=examples)


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )