import logging
import sqlite3
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
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

# Add user to the database if not already there
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
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Function to generate the main menu keyboard
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [  # First row: Solde and Retirer
                KeyboardButton(text="💰 Solde"),
                KeyboardButton(text="🏦 Retirer"),
            ],
            [  # Second row: Inviter, Bonus, Paramètre
                KeyboardButton(text="📨 Inviter"),
                KeyboardButton(text="🎁 Bonus"),
                KeyboardButton(text="⚙️ Paramètre"),
            ],
            [  # Third row: Comment ça marche
                KeyboardButton(text="❓ Comment ça marche"),
            ],
        ],
        resize_keyboard=True,  # Automatically adjust button size
        one_time_keyboard=False  # Keep the keyboard visible
    )

# Update to the send_welcome function
@router.message(Command("start"))
async def send_withdrawal_message():
    random_names = ["Jean", "Marie", "Pierre", "Fatou", "Ali", "Nana", "Paul"]
    random_payment_methods = ["Orange Money", "MTN Mobile Money", "Airtel Money"]
    
    while True:
        try:
            # Generate a random message
            name = random.choice(random_names)
            solde = random.uniform(32000, 50000)  # Random amount above 32000
            payment_method = random.choice(random_payment_methods)
            
            message = (
                f"💳 **Demande de retrait approuvée !**\n\n"
                f"👤 **Nom :** {name}\n"
                f"💰 **Montant :** {solde:.2f} FCFA\n"
                f"📲 **Méthode de paiement :** {payment_method}\n\n"
                f"✅ **Félicitations, votre demande a été traitée avec succès !**"
            )
            
            # Send the message to the channel
            await bot.send_message(chat_id=CHANNEL_ID, text=message)
            
            # Wait for 1 minute before sending the next message
            await asyncio.sleep(60)
        except TelegramAPIError as e:
            logging.error(f"Error sending withdrawal message: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in send_withdrawal_message: {e}")
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    try:
        # Check if the user is a member of the channel
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "creator", "administrator"]:
            # Add the user to the database if not already there
            conn = sqlite3.connect("utilisateurs.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM utilisateurs WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                add_user_to_db(user_id, user_name)
            conn.close()

            # Send a welcome message with the main menu
            await message.reply(
                f"🎉 **Bienvenue à nouveau, {user_name} !** 👋\n\n"
                "✅ **Vous avez maintenant accès à toutes les fonctionnalités du bot.**\n\n"
                 " 👉 ** Inviter vos amis pour commencer a gagner de largen\n\n.**"
                 " 💲 chaque persone inviter vous raporte 500 FCFA\n\n"
                  "vous pouver retirer 🏦 vos gain apartire de 32000 FCFA \n\n"
                 " qu'est-ce que tu attends clic sur 📨 Inviter",
                reply_markup=get_main_menu()
            )
        else:
            # Show subscription prompt with an inline button
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📢 S'abonner à la chaîne",
                            url="https://t.me/YourChannelLink"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="✅ J'ai rejoint",
                            callback_data="check_subscription"
                        )
                    ]
                ]
            )
            await message.reply(
                "🎉 **Bienvenue dans l'aventure des gains  !** 💸\n\n"
                "🌟 **Rejoignez notre chaîne exclusive pour accéder au bot et commencez à gagner de l'argent dès aujourd'hui !**\n\n"
                "💰 **C'est simple : invitez vos amis et gagnez 500 FCFA pour chaque ami invité !** Plus vous partagez, plus vous gagnez ! 🚀\n\n"
                "👉 [Rejoindre la chaîne maintenant](https://t.me/YourChannelLink)\n\n"
                "Après avoir rejoint, cliquez sur **✅ J'ai rejoint**.",
                reply_markup=keyboard
            )
    except TelegramAPIError:
        await message.reply(
            "🚨 **Erreur lors de la vérification. Veuillez réessayer plus tard.**"
        )

# Callback handler for subscription check
@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription(callback_query: types.CallbackQuery):
    # Call `send_welcome` again to recheck subscription
    message = types.Message(
        message_id=callback_query.message.message_id,
        from_user=callback_query.from_user,
        chat=callback_query.message.chat,
        date=callback_query.message.date
    )
    await send_welcome(message)


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
