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
