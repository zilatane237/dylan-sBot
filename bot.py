from aiogram import Bot, Dispatcher,Router ,types
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web

API_TOKEN = "7202157131:AAEgs8msOZmOA0Xpaf9NMYGXJ5g3WWuJndU"


WEBHOOK_HOST = "SOMETHING.COM"
WEBHOOK_PATH =f"/webhook/{API_TOKEN}"
WEBHOOK_URL =f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 5000

bot = Bot(API_TOKEN)
router = Router()

@router.message(commands=["start"])
async def send_welcome(message: type.message):
    await message.reply("welcome i am your friend bot")

async def set_botCommand(bot: Bot):
    commands = [
        BotCommand(commands="/start", description="start the bot")
    ]
    await bot.set_my_commands(commands)

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    await set_botCommand(bot)


async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    dp.setup(app)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    main()