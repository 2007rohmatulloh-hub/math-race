import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter
from aiogram.filters.chat_member_updated import JOIN_TRANSITION
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated


API_TOKEN = "8602948149:AAHGCR5a-sCgs3wKo5d6FYUc_ZffzxQO4Ww"

CHANNEL_ID = -1002973042972
MAIN_CHANNEL_LINK = "https://t.me/+yKejphFq__MwOGUy"
MARAFON_GROUP_LINK = "https://t.me/+gVFz9nv8h1NlNjIy"

REQUIRED_INVITES = 3


# 🔥 ДОБАВЛЕНО
CHANNELS = [
    CHANNEL_ID,
    -1002222222222,
    -1003333333333
]

CHANNEL_LINKS = [
    MAIN_CHANNEL_LINK ,
    "https://t.me/kanal2",
    "https://t.me/kanal3"
]


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# 🔥 ПРОВЕРКА ПОДПИСКИ
async def check_subscriptions(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


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

    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users (user_id, referrer_id) VALUES (?,?)",
            (user_id, referrer_id)
        )

    conn.commit()
    conn.close()

    link = await create_start_link(bot, str(user_id), encode=True)

    kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanal 1", url=CHANNEL_LINKS[0])],
        [InlineKeyboardButton(text="📢 Kanal 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton(text="📢 Kanal 3", url=CHANNEL_LINKS[2])],
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=f"https://t.me/share/url?url={link}&text=Kitob marafoniga qo'shiling!")],
        [InlineKeyboardButton(text="📊 Reyting", callback_data="rating")],
        [InlineKeyboardButton(text="✅ Natijani tekshirish", callback_data="check")]
    ]
    )

    text = f"""

✨ *Kitobxon qizlar jamoasi* bilan birgalikda kunlik mutolaa qilib,
kitobxonlik ko‘nikmasini shakllantirish-chi?

📖 Unda sizni birgalikda ko‘plab kitoblarni o‘qib,  
oxirida o‘sha kitoblar bo‘yicha testlar,  
sertifikatlar va sovg‘alarni qo‘lga kiritadigan  
Kitobxon qizlar jamoasiga taklif qilamiz! 🎀

🚀 Jamoaga qo‘shilishga tayyormisiz?

Unda quyidagi havolani do‘stlaringizga yuboring  
va 3 ta do‘stingizni taklif qiling 👇

🔗 `{link}`

🎁 3 ta do‘stingiz kanalga qo‘shilgach sizga maxsus guruh havolasi beriladi!

📚 Aytgancha, bu kanalda bepul arab tili darslari ham bor.**
""" 

    await message.answer(text, reply_markup=kb)


# USER JOIN CHANNEL
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
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

    is_subscribed = await check_subscriptions(user_id)

    if not is_subscribed:
        await callback.answer(
            "❗ Iltimos, barcha 3 ta kanalga a'zo bo‘ling",
            show_alert=True
        )
        return

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


# 🔥 РЕЙТИНГ
@dp.callback_query(F.data == "rating")
async def rating(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, invited_count
        FROM users
        ORDER BY invited_count DESC
        LIMIT 10
    """)
    top = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*) + 1
        FROM users
        WHERE invited_count > (
            SELECT invited_count FROM users WHERE user_id=?
        )
    """, (user_id,))
    place = cur.fetchone()[0]

    cur.execute("SELECT invited_count FROM users WHERE user_id=?", (user_id,))
    my = cur.fetchone()
    my_count = my[0] if my else 0

    conn.close()

    text = "🏆 TOP 10:\n\n"

    for i, user in enumerate(top, 1):
        text += f"{i}. {user[0]} — {user[1]}\n"

    text += f"\n📊 Sizning natijangiz:\n"
    text += f"Joy: {place}\nTakliflar: {my_count}"

    await callback.message.answer(text)


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