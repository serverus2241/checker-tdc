import paypalrestsdk
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configurar la API de PayPal con las credenciales de producción
paypalrestsdk.configure({
    "mode": "live",  # Cambia a "sandbox" para pruebas
    "client_id": "YOUR_LIVE_CLIENT_ID",
    "client_secret": "YOUR_LIVE_CLIENT_SECRET"
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame el número de tarjeta de crédito, fecha de vencimiento (MM/YY) y CVV separados por comas para verificar si está aprobada.")

async def check_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Obtener los datos de la tarjeta de crédito del mensaje
        card_info = update.message.text.strip().split(',')
        if len(card_info) != 3:
            await update.message.reply_text("Por favor, ingresa los datos en el formato correcto: número de tarjeta, MM/YY, CVV.")
            return

        card_number = card_info[0].strip()
        expire_month, expire_year = card_info[1].strip().split('/')
        cvv = card_info[2].strip()

        # Crear una autorización de pago con PayPal
        payment = paypalrestsdk.Payment({
            "intent": "authorize",
            "payer": {
                "payment_method": "credit_card",
                "funding_instruments": [{
                    "credit_card": {
                        "number": card_number,
                        "type": "visa",  # Cambia según el tipo de tarjeta
                        "expire_month": expire_month,
                        "expire_year": "20" + expire_year,  # Formato completo del año
                        "cvv2": cvv,
                        "first_name": "John",
                        "last_name": "Doe"
                    }
                }]
            },
            "transactions": [{
                "amount": {
                    "total": "1.00",
                    "currency": "USD"
                },
                "description": "Tarjeta de prueba"
            }]
        })

        # Intentar realizar la autorización
        if payment.create():
            authorization_id = payment.transactions[0].related_resources[0].authorization.id
            card_type = payment.payer.funding_instruments[0].credit_card.type
            country = payment.payer.funding_instruments[0].credit_card.country_code
            await update.message.reply_text(f"La tarjeta de crédito está aprobada.\nTipo: {card_type.upper()}\nPaís: {country}")
            
            # Anular la autorización para liberar los fondos
            authorization = paypalrestsdk.Authorization.find(authorization_id)
            if authorization.void():
                await update.message.reply_text("La autorización ha sido anulada y los fondos han sido liberados.")
            else:
                await update.message.reply_text("No se pudo anular la autorización automáticamente. Por favor, revisa manualmente.")
        else:
            await update.message.reply_text(f"La tarjeta de crédito está declinada: {payment.error['message']}")
    except Exception as e:
        await update.message.reply_text(f"Error al procesar la tarjeta de crédito: {str(e)}")

def main():
    # Reemplaza 'YOUR_TELEGRAM_TOKEN' con tu token de Telegram
    application = ApplicationBuilder().token("YOUR_TELEGRAM_TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_card))

    application.run_polling()

if __name__ == '__main__':
    main()
