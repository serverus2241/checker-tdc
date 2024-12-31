import streamlit as st
import paypalrestsdk
import requests

# Función para obtener la información del banco emisor usando el número de tarjeta
def get_bank_info(card_number):
    bin_number = card_number[:6]
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al consultar BIN: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con Binlist: {e}")
    return None

# Función para mapear los tipos de tarjeta a valores aceptados por PayPal
def map_card_type(card_type):
    card_type = card_type.lower()
    mapping = {
        "visa": "VISA",
        "mastercard": "MASTERCARD",
        "amex": "AMEX",
        "discover": "DISCOVER",
        "diners": "DINERS",
        "maestro": "MAESTRO",
        "jcb": "JCB"
    }
    return mapping.get(card_type, "null")

# Configurar la API de PayPal usando claves desde Streamlit Secrets
paypalrestsdk.configure({
    "mode": "live",  # Cambia a "live" para producción
    "client_id": st.secrets["PAYPAL_CLIENT_ID"],
    "client_secret": st.secrets["PAYPAL_CLIENT_SECRET"]
})

st.title("Verificación de Tarjetas de Crédito")
st.write("Ingrese los detalles de la tarjeta para verificar si está aprobada o declinada.")

# Formulario para ingresar detalles de la tarjeta
card_number = st.text_input("Número de la Tarjeta de Crédito")
expire_month = st.selectbox("Mes de Vencimiento (MM)", [f"{i:02d}" for i in range(1, 13)])
current_year = 2024  # Año actual, cámbialo según sea necesario
expire_year = st.selectbox("Año de Vencimiento (YY)", [f"{i:02d}" for i in range(current_year % 100, (current_year + 10) % 100)])
cvv = st.text_input("CVV", type="password")

# Botón para verificar la tarjeta
if st.button("Verificar Tarjeta"):
    if card_number and expire_month and expire_year and cvv:
        try:
            # Obtener información del banco emisor
            bank_info = get_bank_info(card_number)
            if bank_info:
                bank_name = bank_info.get('bank', {}).get('name', 'Desconocido')
                country = bank_info.get('country', 'Desconocido')
                card_type = bank_info.get('scheme', 'Desconocido').capitalize()
            else:
                bank_name = 'No disponible'
                country = 'No disponible'
                card_type = 'Desconocido'

            # Mapear el tipo de tarjeta a un valor aceptado por PayPal
            card_type_paypal = map_card_type(card_type)
            if card_type_paypal == "null":
                st.warning(f"Tipo de tarjeta no soportado: {card_type}")
            else:
                # Intentar realizar la autorización
                payment = paypalrestsdk.Payment({
                    "intent": "authorize",
                    "payer": {
                        "payment_method": "credit_card",
                        "funding_instruments": [{
                            "credit_card": {
                                "number": card_number,
                                "type": card_type_paypal,  # Usa el tipo de tarjeta mapeado
                                "expire_month": expire_month,
                                "expire_year": "20" + expire_year,
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

                if payment.create():
                    st.success("La tarjeta de crédito está aprobada.")
                    st.write(f"- **Banco Emisor**: {bank_name}")
                    st.write(f"- **País**: {country}")
                    st.write(f"- **Tipo de Tarjeta**: {card_type}")
                else:
                    error_message = payment.error.get('message', 'Error desconocido')
                    st.error("La tarjeta de crédito está declinada.")
                    st.error(f"Detalles del error: {error_message}")

        except Exception as e:
            st.error(f"Error al procesar la tarjeta: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
