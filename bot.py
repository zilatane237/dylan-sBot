import logging
import sqlite3
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.exceptions import TelegramAPIError

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace with your actual bot token
API_TOKEN = "7610826102:AAFe8Oy5aqF5AdxdDI1O9VG1oX5K-4Oz76w"

# Webhook settings
WEBHOOK_HOST = "https://dylan-sbot-2.onrender.com"  # Replace with your Render app URL
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Web server settings
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 5000

# Initialize Bot and Router
bot = Bot(token=API_TOKEN)
router = Router()

# Replace 'CHANNEL_ID' with your actual channel ID (must be an integer starting with -100)
CHANNEL_ID = -1002340148619  # Replace with your channel's ID

# Create and initialize the SQLite database
def init_db():
    conn = sqlite3.connect("utilisateurs.db")  # Database named "utilisateurs.db"
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY,
            nom TEXT,
            sold REAL DEFAULT 0.0,  -- "sold" for balance
            invite INTEGER DEFAULT 0  -- "invite" for number of invitations
        )
    """)
    conn.commit()
    conn.close()

# Add user to the database if they are not already there
def add_user_to_db(user_id, user_name):
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilisateurs WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO utilisateurs (id, nom) VALUES (?, ?)", (user_id, user_name))
        conn.commit()
    conn.close()

# Start command handler
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "creator", "administrator"]:
            add_user_to_db(user_id, user_name)
            await message.reply(f"🎉 **Bienvenue à nouveau, {user_name} !** 👋\n\n"
                                "💪 **Vous êtes déjà membre de notre chaîne. Bravo !**\n\n"
                                "👉 **Continuez à inviter vos amis pour accumuler vos gains.** Chaque ami invité vous rapporte **500 FCFA** !\n\n"
                                "💸 **Une fois que vous avez assez d'invitations, vous pourrez faire votre premier retrait !** 🚀\n\n"
                                "📢 **Invitez plus et commencez à gagner maintenant !** 🌟")
        else:
            add_user_to_db(user_id, user_name)
            await message.reply(
                "🎉 **Bienvenue dans l'aventure des gains  !** 💸\n\n"
                "🌟 **Rejoignez notre chaîne exclusive pour accéder au bot et commencez à gagner de l'argent dès aujourd'hui !**\n\n"
                "💰 **C'est simple : invitez vos amis et gagnez 500 FCFA pour chaque ami invité !** Plus vous partagez, plus vous gagnez ! 🚀\n\n"
                "👉 **[Rejoindre la chaîne maintenant](https://t.me/weirdbottest)** et démarrez votre voyage vers des revenus illimités ! 🎯"
            )
    except TelegramAPIError as e:
        await message.reply(
            "veuillez rejoindre notre chaîne pour avoir accès au bot et commencer à gagner de l'argent en invitant vos amis. Vous pouvez gagner 500 FCFA par ami invité !\n\n"
            "👉 [Rejoindre la chaîne](https://t.me/YourChannelLink)"
        )

# Set bot commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Démarrer le bot"),
    ]
    await bot.set_my_commands(commands)

# Main application setup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    await set_commands(bot)
    init_db()

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    dp = Dispatcher()
    dp.include_router(router)
    print("bot.....")
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    main()
