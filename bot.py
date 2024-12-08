from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import sqlite3


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
            sold REAL DEFAULT 32000.0,  -- "sold" for balance
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

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    try:
        # Check if the user is a member of the channel
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "creator", "administrator"]:
            # Add the user to the database if not already there
            add_user_to_db(user_id, user_name)

            # Send a welcome message with the main menu
            await message.reply(
                f"🎉 **Bienvenue à nouveau, {user_name} !** 👋\n\n"
                "✅ **Vous avez maintenant accès à toutes les fonctionnalités du bot.**\n\n"
                "👉 **Invitez vos amis pour commencer à gagner de l'argent.** 💲\n\n"
                "💲 Chaque personne invitée vous rapporte **500 FCFA**.\n\n"
                "🏦 Vous pouvez retirer vos gains à partir de **32,000 FCFA**.\n\n"
                "🎯 Qu'est-ce que tu attends ? Cliquez sur 📨 **Inviter**.",
                reply_markup=get_main_menu()
            )
        else:
            # Show subscription prompt with an inline button
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📢 S'abonner à la chaîne",
                            url="https://t.me/weirdbottest"
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
                "👉 [Rejoindre la chaîne maintenant](https://t.me/weirdbottest)\n\n"
                "Après avoir rejoint, cliquez sur **✅ J'ai rejoint**.",
                reply_markup=keyboard
            )
    except TelegramAPIError:
        await message.reply(
            "🚨 **Erreur lors de la vérification. Veuillez réessayer plus tard.**"
        )

# Callback handler for the buttons
@router.message(lambda message: message.text in ["💰 Solde", "🏦 Retirer", "📨 Inviter", "🎁 Bonus", "⚙️ Paramètre", "❓ Comment ça marche"])
async def handle_buttons(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if message.text == "📨 Inviter":
        # Generate the invitation link for the user
        invitation_link = generate_invitation_link(user_id)
        
        # Send the invitation message
        await message.reply(
            f"🎉 **Salut {user_name}!** 👋\n\n"
            "👉 **Invitez vos amis et commencez à gagner de l'argent dès maintenant!** 💸\n\n"
            "💲 **Chaque ami invité vous rapporte 500 FCFA.** Plus vous invitez, plus vous gagnez! 🚀\n\n"
            "📨 **Voici votre lien d'invitation unique:**\n"
            f"🔗 {invitation_link}\n\n"
            "Partagez ce lien avec vos amis pour qu'ils rejoignent le bot et commencez à accumuler vos gains!",
        )
        
    elif message.text == "💰 Solde":
        # Get the user's balance from the database
        conn = sqlite3.connect("utilisateurs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT sold FROM utilisateurs WHERE id = ?", (user_id,))
        user_balance = cursor.fetchone()
        conn.close()

        # If no balance found, inform the user
        if user_balance is None:
            await message.reply("🚨 **Erreur : Votre solde n'a pas pu être récupéré. Veuillez réessayer plus tard.**")
            return

        # Extract balance value
        user_balance = user_balance[0]

        # Check if the user has reached the minimum amount for withdrawal
        min_withdrawal = 32000  # Define the minimum withdrawal threshold in FCFA

        if user_balance >= min_withdrawal:
            # Congratulatory message for reaching the withdrawal threshold
            await message.reply(
                f"🎉 **Félicitations {user_name}!** 👏\n\n"
                f"Vous avez un solde de **{user_balance} FCFA**, ce qui vous permet de faire un retrait.\n\n"
                "👉 **Cliquez sur 🏦 Retirer pour retirer vos fonds.**"
            )
        else:
            # Encouragement message for users who haven't reached the withdrawal threshold
            await message.reply(
                f"💰 **Votre solde actuel est de {user_balance} FCFA.**\n\n"
                "🚀 **Il vous reste encore à accumuler des gains pour atteindre le seuil de retrait de 32,000 FCFA.**\n\n"
                "👉 **Continuez à inviter vos amis et vous gagnerez plus!** 💸"
            )

    elif message.text == "🏦 Retirer":
        # Get the user's balance from the database again
        conn = sqlite3.connect("utilisateurs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT sold FROM utilisateurs WHERE id = ?", (user_id,))
        user_balance = cursor.fetchone()
        conn.close()

        # If no balance found, inform the user
        if user_balance is None:
            await message.reply("🚨 **Erreur : Votre solde n'a pas pu être récupéré. Veuillez réessayer plus tard.**")
            return

        user_balance = user_balance[0]

        # Check if the user has enough balance to withdraw
        min_withdrawal = 32000  # Define the minimum withdrawal threshold in FCFA

        if user_balance >= min_withdrawal:
            # Ask for the user's phone number if they are eligible for withdrawal
            await message.reply(
                f"🎉 **Félicitations {user_name}!** 👏\n\n"
                f"Vous avez un solde de **{user_balance} FCFA**, ce qui vous permet de faire un retrait.\n\n"
                "👉 **Veuillez entrer votre numéro de téléphone pour compléter votre demande de retrait.**\n\n"
                "⚠️ Assurez-vous que le numéro soit valide (au moins 9 chiffres et uniquement des chiffres)."
            )

            # Set state to expect phone number input
            await state.set_state("waiting_for_phone_number")
        else:
            # Inform user they have not reached the minimum threshold
            await message.reply(
                f"💰 **Votre solde actuel est de {user_balance} FCFA.**\n\n"
                "🚀 **Il vous reste encore à accumuler des gains pour atteindre le seuil de retrait de 32,000 FCFA.**\n\n"
                "👉 **Continuez à inviter vos amis et vous gagnerez plus!** 💸"
            )

    elif message.text == "🎁 Bonus":
        # Empty response for Bonus button
        await message.reply("🎁 **Bonus** feature is not yet implemented.")

    elif message.text == "⚙️ Paramètre":
        # Empty response for Paramètre button
        await message.reply("⚙️ **Paramètre** feature is not yet implemented.")

    elif message.text == "❓ Comment ça marche":
        # Empty response for Comment ça marche button
        await message.reply("❓ **Comment ça marche** feature is not yet implemented.")

# Handler for user's phone number input
@router.message(state="waiting_for_phone_number")
async def handle_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    phone_number = message.text.strip()

    # Validate phone number (only digits, minimum 9 digits)
    if not phone_number.isdigit() or len(phone_number) < 9:
        await message.reply("❌ **Numéro de téléphone invalide. Assurez-vous qu'il contient uniquement des chiffres et au moins 9 chiffres.**")
        return

    # Save the phone number in the database
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE utilisateurs SET phone_number = ? WHERE id = ?", (phone_number, user_id))
    conn.commit()
    conn.close()

    # Send confirmation to the user
    await message.reply(
        f"✅ **Votre demande de retrait est en cours {user_name}!**\n\n"
        "Nous avons bien reçu votre numéro de téléphone et votre retrait est en traitement.\n\n"
        "💸 **Félicitations pour votre succès!** Le retrait sera effectué sous peu."
    )

    # Send a notification to the channel
    masked_phone = mask_phone_number(phone_number)
    await send_withdrawal_notification(user_name, user_balance, masked_phone)

    # Reset state
    await state.finish()

# Function to send withdrawal notification to the channel
async def send_withdrawal_notification(user_name, amount, masked_phone):
    try:
        await bot.send_message(
            '@weirdbottest',  # Replace with your actual channel ID
            f"📢 **Nouvelle demande de retrait réussie!**\n\n"
            f"🧑‍💼 **Nom:** {user_name}\n"
            f"💰 **Montant demandé:** {amount} FCFA\n"
            f"📞 **Numéro de téléphone:** {masked_phone}\n\n"
            "💸 **Retrait en traitement!**"
        )
    except ChatNotFound:
        print("Channel not found. Please check the channel ID.")

# Helper function to mask the last 5 digits of the phone number
def mask_phone_number(phone_number):
    if len(phone_number) >= 5:
        return phone_number[:-5] + "*****"
    return phone_number

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
