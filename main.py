import asyncio
import sqlite3
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter
from aiogram.filters.chat_member_updated import JOIN_TRANSITION
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated


API_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = -1002973042972
MAIN_CHANNEL_LINK = "https://t.me/+yKejphFq__MwOGUy"
MARAFON_GROUP_LINK = "https://t.me/+gVFz9nv8h1NlNjIy"

REQUIRED_INVITES = 5


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# DATABASE
def init_db():
    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER,
        invited_count INTEGER DEFAULT 0,
        is_counted INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# START
@dp.message(CommandStart())
async def start_handler(message: types.Message):

    user_id = message.from_user.id
    args = message.text.split()

    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    referrer_id = None

    if len(args) > 1:
        try:
            payload = decode_payload(args[1])

            if payload.isdigit():
                referrer_id = int(payload)

        except:

            if args[1].isdigit():
                referrer_id = int(args[1])

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    if not user:

        cur.execute(
            "INSERT INTO users (user_id, referrer_id) VALUES (?,?)",
            (user_id, referrer_id)
        )

    else:

        cur.execute(
            "SELECT referrer_id FROM users WHERE user_id=?",
            (user_id,)
        )

        old_ref = cur.fetchone()

        if old_ref and old_ref[0] is None and referrer_id:

            cur.execute(
                "UPDATE users SET referrer_id=? WHERE user_id=?",
                (referrer_id, user_id)
            )

    conn.commit()
    conn.close()

    link = await create_start_link(
        bot,
        str(user_id),
        encode=True
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga a'zo bo'lish",
                    url=MAIN_CHANNEL_LINK
                )
            ],

            [
                InlineKeyboardButton(
                    text="📤 Do'stlarga ulashish",
                    url=f"https://t.me/share/url?url={link}&text=Kitob marafoniga qo'shiling!"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Natijani tekshirish",
                    callback_data="check"
                )
            ]
        ]
    )

    text = f"""

✨ *Kitobxon qizlar jamoasi* bilan birgalikda kunlik mutolaa qilib,
kitobxonlik ko‘nikmasini shakllantirish-chi?

📖 Unda sizni birgalikda ko‘plab kitoblarni o‘qib,
oxirida o‘sha kitoblar bo‘yicha **testlar**,
**sertifikatlar** va **sovg‘alarni** qo‘lga kiritadigan
**Kitobxon qizlar jamoasiga taklif qilamiz!** 🎀

🚀 **Jamoaga qo‘shilishga tayyormisiz?**

Unda quyidagi havolani do‘stlaringizga yuboring
va **5 ta do‘stingizni taklif qiling** 👇

🔗 `{link}`

🎁 5 ta do‘stingiz kanalga qo‘shilgach sizga **maxsus guruh havolasi** beriladi!

📚 Aytgancha, bu kanalda **bepul arab tili darslari ham bor.**
"""

    await message.answer(
        text,
        reply_markup=kb
    )


# USER JOIN CHANNEL
@dp.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=JOIN_TRANSITION
    )
)
async def user_join(event: ChatMemberUpdated):

    if event.chat.id != CHANNEL_ID:
        return

    user_id = event.new_chat_member.user.id

    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT referrer_id, is_counted FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cur.fetchone()

    if data:

        referrer_id, counted = data

        if referrer_id and counted == 0:

            cur.execute(
                "UPDATE users SET invited_count = invited_count + 1 WHERE user_id=?",
                (referrer_id,)
            )

            cur.execute(
                "UPDATE users SET is_counted = 1 WHERE user_id=?",
                (user_id,)
            )

            conn.commit()

            try:

                await bot.send_message(
                    referrer_id,
                    "🎉 Siz yangi odam taklif qildingiz! +1"
                )

            except:
                pass

    conn.close()


# CHECK BUTTON
@dp.callback_query(F.data == "check")
async def check(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT invited_count FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    count = row[0] if row else 0

    conn.close()

    if count >= REQUIRED_INVITES:

        await callback.message.answer(
            f"🎉 Tabriklayman!\n\nMana guruh havolasi:\n{MARAFON_GROUP_LINK}"
        )

    else:

        await callback.answer(
            f"Siz {count}/{REQUIRED_INVITES} odam taklif qildingiz",
            show_alert=True
        )


# STATS
@dp.message(Command("stats"))
async def stats(message: types.Message):

    user_id = message.from_user.id

    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT invited_count FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    count = row[0] if row else 0

    conn.close()

    await message.answer(
        f"📊 Siz {count} ta odam taklif qilgansiz."
    )


# MAIN
async def main():

    init_db()

    print("Bot ishga tushdi...")

    await dp.start_polling(
        bot,
        allowed_updates=[
            "message",
            "callback_query",
            "chat_member"
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
