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
# Main button handler
@router.message(lambda message: message.text in ["💰 Solde", "🏦 Retirer", "📨 Inviter", "🎁 Bonus", "⚙️ Paramètre", "❓ Comment ça marche"])
async def handle_buttons(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Handle different buttons
    if message.text == "🏦 Retirer":
        # Connect to the database and fetch user's balance
        conn = sqlite3.connect("utilisateurs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT sold FROM utilisateurs WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            user_balance = user_data[0]  # Fetch balance
            if user_balance >= 32000:  # Minimum balance for withdrawal
                # Notify user to provide their phone number
                await message.reply(
                    "🎉 **Félicitations, vous avez atteint le montant minimum pour un retrait !** 💸\n\n"
                    "Veuillez entrer votre numéro de téléphone pour effectuer le retrait. 📞"
                )

                # Add state to track phone number input
                @router.message(lambda msg: msg.text.isdigit() and len(msg.text) >= 10)
                async def handle_phone_number(msg: types.Message):
                    phone_number = msg.text
                    # Update the database with the phone number
                    cursor.execute(
                        "UPDATE utilisateurs SET sold = sold - 32000 WHERE id = ?",
                        (user_id,)
                    )
                    conn.commit()
                    conn.close()

                    # Send a confirmation message to the channel
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=(
                            f"📢 **Demande de Retrait** 💵\n\n"
                            f"👤 **Nom :** {user_name}\n"
                            f"💰 **Solde :** 32,000 FCFA\n"
                            f"📱 **Mode de Paiement :** Paiement Mobile\n"
                            f"📞 **Numéro de Téléphone :** {phone_number}\n\n"
                            f"✅ **Veuillez traiter cette demande de paiement.**"
                        )
                    )

                    # Notify the user of the successful withdrawal process
                    await msg.reply(
                        "✅ **Votre demande de retrait a été soumise avec succès !** 💸\n\n"
                        "Un message a été envoyé à l'administrateur. Vous recevrez votre paiement sous peu. Merci ! 🙏"
                    )

                    # Unregister the phone number handler after use
                    router.message.unregister(handle_phone_number)
            else:
                # Notify user of insufficient balance
                await message.reply(
                    "❌ **Désolé, votre solde est insuffisant pour un retrait.**\n\n"
                    f"💰 **Votre solde actuel :** {user_balance} FCFA\n"
                    f"👉 **Montant minimum requis :** 32,000 FCFA\n\n"
                    "Continuez à inviter des amis pour accumuler plus de gains ! 🚀"
                )
        else:
            conn.close()
            # Notify user if they are not found in the database
            await message.reply(
                "❌ **Erreur : Vous n'êtes pas enregistré dans notre base de données.**\n\n"
                "Veuillez redémarrer le bot en utilisant la commande /start."
            )
    elif message.text == "💰 Solde":
        # Example response for balance check
        conn = sqlite3.connect("utilisateurs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT sold FROM utilisateurs WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            user_balance = user_data[0]
            await message.reply(f"💰 **Votre solde actuel est de {user_balance} FCFA.**")
        else:
            await message.reply("❌ **Vous n'êtes pas enregistré dans notre base de données.**")
    elif message.text == "📨 Inviter":
        await message.reply(
            "📨 **Invitez vos amis et gagnez !**\n\n"
            "Envoyez votre lien d'invitation et gagnez 500 FCFA pour chaque ami inscrit ! 🚀"
        )
    elif message.text == "🎁 Bonus":
        await message.reply(
            "🎁 **Bonus quotidien !**\n\n"
            "Vérifiez votre compte tous les jours pour recevoir des bonus exclusifs ! 🌟"
        )
    elif message.text == "⚙️ Paramètre":
        await message.reply(
            "⚙️ **Paramètres**\n\n"
            "Utilisez cette section pour mettre à jour vos préférences et informations. 📖"
        )
    elif message.text == "❓ Comment ça marche":
        await message.reply(
            "❓ **Comment ça marche**\n\n"
            "1️⃣ Invitez vos amis à rejoindre le bot.\n"
            "2️⃣ Gagnez 500 FCFA par ami inscrit.\n"
            "3️⃣ Retirez vos gains dès que vous atteignez 32,000 FCFA.\n\n"
            "📈 Plus vous invitez, plus vous gagnez !"
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
