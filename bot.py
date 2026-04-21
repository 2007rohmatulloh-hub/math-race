# 8684302400:AAGYWoBEF_UGS6Da960lou2Uqb_fHDYOO7Y
import os
import asyncio
import time
import sqlite3
from random import randint, shuffle

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

# ================= DATABASE =================
conn = sqlite3.connect("game.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    user_id INTEGER,
    username TEXT,
    score INTEGER,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1
)
""")

conn.commit()

# ================= START =================
@dp.message(CommandStart())
async def start(message: types.Message):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Start Game", callback_data="start")],
        [InlineKeyboardButton(text="🏆 Leaderboard", callback_data="top")]
    ])

    await message.answer("🧮 Math Race Bot", reply_markup=kb)

# ================= LEVEL =================
@dp.callback_query(lambda c: c.data == "start")
async def choose_level(callback: CallbackQuery):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Easy", callback_data="easy")],
        [InlineKeyboardButton(text="🟡 Medium", callback_data="medium")],
        [InlineKeyboardButton(text="🔴 Hard", callback_data="hard")]
    ])

    await callback.message.answer("Darajani tanlang:", reply_markup=kb)
    await callback.answer()

# ================= COUNT =================
@dp.callback_query(lambda c: c.data in ["easy", "medium", "hard"])
async def choose_amount(callback: CallbackQuery):

    user_id = callback.from_user.id
    username = callback.from_user.username or "NoName"

    users[user_id] = {
        "level": callback.data,
        "username": username
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5", callback_data="q_5")],
        [InlineKeyboardButton(text="7", callback_data="q_7")],
        [InlineKeyboardButton(text="10", callback_data="q_10")],
        [InlineKeyboardButton(text="15", callback_data="q_15")]
    ])

    await callback.message.answer("Nechta savol?", reply_markup=kb)
    await callback.answer()

# ================= START GAME =================
@dp.callback_query(lambda c: c.data.startswith("q_"))
async def start_game(callback: CallbackQuery):

    user_id = callback.from_user.id
    total = int(callback.data.split("_")[1])

    users[user_id].update({
        "score": 0,
        "question": 1,
        "total": total
    })

    await send_question(callback.message, user_id)
    await callback.answer()

# ================= QUESTION =================
async def send_question(message, user_id):

    data = users[user_id]
    level = data["level"]

    if level == "easy":
        x, y = randint(1, 10), randint(1, 10)
    elif level == "medium":
        x, y = randint(5, 20), randint(5, 15)
    else:
        x, y = randint(10, 50), randint(10, 20)

    correct = x * y
    data["answer"] = correct
    data["start_time"] = time.time()

    options = [
        correct,
        correct + randint(1, 5),
        correct - randint(1, 5),
        correct + randint(6, 10)
    ]
    shuffle(options)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(opt), callback_data=f"ans_{opt}")]
        for opt in options
    ])

    await message.answer(
        f"🧮 {data['question']}/{data['total']}\n{x} * {y} = ?",
        reply_markup=kb
    )

# ================= XP SYSTEM =================
def add_xp(user_id, username, score):

    xp_gain = score * 10

    cursor.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        xp, level = row
    else:
        xp, level = 0, 1

    xp += xp_gain
    new_level = xp // 100 + 1

    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, username, xp, level)
    VALUES (?, ?, ?, ?)
    """, (user_id, username, xp, new_level))

    conn.commit()

    return xp, new_level

# ================= ACHIEVEMENTS =================
def check_achievements(score):

    achievements = []

    if score >= 50:
        achievements.append("🏆 Master")
    if score >= 30:
        achievements.append("⚡ Fast Brain")
    if score == 0:
        achievements.append("😅 Try Again")

    return achievements

# ================= ANSWER =================
@dp.callback_query(lambda c: c.data.startswith("ans_"))
async def answer(callback: CallbackQuery):

    user_id = callback.from_user.id

    if user_id not in users:
        return

    data = users[user_id]
    user_answer = int(callback.data.split("_")[1])
    correct = data["answer"]

    time_spent = time.time() - data["start_time"]

    if user_answer == correct:
        data["score"] += 1

        if time_spent < 3:
            data["score"] += 2
        elif time_spent < 5:
            data["score"] += 1

        await callback.message.answer("✅ To‘g‘ri!")
    else:
        await callback.message.answer(f"❌ Xato! {correct}")

    data["question"] += 1

    # ================= END GAME =================
    if data["question"] > data["total"]:

        score = data["score"]
        username = data["username"]

        # save score
        cursor.execute(
            "INSERT INTO scores VALUES (?, ?, ?, date('now'))",
            (user_id, username, score)
        )
        conn.commit()

        xp, level = add_xp(user_id, username, score)
        achievements = check_achievements(score)

        percent = score / data["total"]

        if percent == 1:
            msg = "🔥 PERFECT!"
        elif percent >= 0.7:
            msg = "💪 Juda yaxshi!"
        elif percent >= 0.4:
            msg = "🙂 Yomon emas"
        else:
            msg = "😅 Mashq qiling!"

        ach_text = "\n".join(achievements) if achievements else "—"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Play Again", callback_data="start")]
        ])

        await callback.message.answer(
            f"""
🏁 O‘yin tugadi!

👤 {username}
Score: {score}

⭐ XP: {xp}
🎯 Level: {level}

🏆 Achievements:
{ach_text}

{msg}
""",
            reply_markup=kb
        )

        users.pop(user_id)

    else:
        await send_question(callback.message, user_id)

    await callback.answer()

# ================= LEADERBOARD =================
@dp.callback_query(lambda c: c.data == "top")
async def leaderboard(callback: CallbackQuery):

    cursor.execute("""
    SELECT username, xp
    FROM users
    ORDER BY xp DESC
    LIMIT 5
    """)

    rows = cursor.fetchall()

    text = "🏆 TOP PLAYERS:\n\n"

    for i, (name, xp) in enumerate(rows, 1):
        text += f"{i}. {name} — {xp} XP\n"

    await callback.message.answer(text)
    await callback.answer()

# ================= PROFILE =================
@dp.message(Command("profile"))
async def profile(message: types.Message):

    user_id = message.from_user.id

    cursor.execute("SELECT username, xp, level FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        await message.answer("No data yet")
        return

    username, xp, level = row

    await message.answer(
        f"""
👤 {username}

⭐ XP: {xp}
🎯 Level: {level}
"""
    )

# ================= MONTH STATS =================
@dp.message(Command("stats"))
async def stats(message: types.Message):

    cursor.execute("""
    SELECT COUNT(DISTINCT user_id)
    FROM scores
    WHERE date >= date('now', '-30 day')
    """)

    count = cursor.fetchone()[0]

    await message.answer(f"📊 Oxirgi 30 kunda: {count} foydalanuvchi")

# ================= MAIN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    import os
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()
