import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command 
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.exceptions import TelegramAPIError

# Set up logging
#logging.basicConfig(level=logging.INFO)

# Replace with your actual bot token
API_TOKEN = "7202157131:AAEgs8msOZmOA0Xpaf9NMYGXJ5g3WWuJndU"

# Webhook settings
WEBHOOK_HOST = "https://dylan-sbot-1.onrender.com"  # Replace with your Render app URL
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

# Start command handler
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
        if member.status in ["member", "creator", "administrator"]:
            await message.reply("hello")
        else:
            await message.reply(
                "🎉 **Bienvenue dans l'aventure des gains  !** 💸\n\n"
                "🌟 **Rejoignez notre chaîne exclusive pour accéder au bot et commencez à gagner de l'argent dès aujourd'hui !**\n\n"
                "💰 **C'est simple : invitez vos amis et gagnez 500 FCFA pour chaque ami invité !** Plus vous partagez, plus vous gagnez ! 🚀\n\n"
                "👉 **[Rejoindre la chaîne maintenant](https://t.me/YourChannelLink)** et démarrez votre voyage vers des revenus illimités ! 🎯"
            )
    except TelegramAPIError as e:
        # Handle the case where the bot is not a member of the channel or user hasn't interacted with the bot
        await message.reply(
            "euillez rejoindre notre chaîne pour avoir accès au bot et commencer à gagner de l'argent en invitant vos amis. Vous pouvez gagner 500 FCFA par ami invité !\n\n"
            "👉 [Rejoindre la chaîne](https://t.me/YourChannelLink)"
        )

# Set bot commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start the bot"),
    ]
    await bot.set_my_commands(commands)

# Main application setup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    await set_commands(bot)

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
