import streamlit as st
import paypalrestsdk
import pycountry
import requests

def get_country_flag(country_code):
    country = pycountry.countries.get(alpha_2=country_code)
    if country:
        # Convertir el código del país en un emoji de bandera
        return chr(127462 + ord(country.alpha_2[0]) - ord('A')) + chr(127462 + ord(country.alpha_2[1]) - ord('A'))
    return ""

def get_bank_info(card_number):
    bin_number = card_number[:6]
    response = requests.get(f"https://lookup.binlist.net/{bin_number}")
    if response.status_code == 200:
        return response.json()
    return None

# Función para mapear los tipos de tarjeta a valores aceptados por PayPal
def map_card_type(card_type):
    card_type = card_type.lower()
    if card_type == "visa":
        return "VISA"
    elif card_type == "mastercard":
        return "MASTERCARD"
    elif card_type == "amex":
        return "AMEX"
    elif card_type == "discover":
        return "DISCOVER"
    elif card_type == "diners":
        return "DINERS"
    elif card_type == "maestro":
        return "MAESTRO"
    elif card_type == "elo":
        return "ELO"
    elif card_type == "hiper":
        return "HIPER"
    elif card_type == "switch":
        return "SWITCH"
    elif card_type == "jcb":
        return "JCB"
    elif card_type == "hipercard":
        return "HIPERCARD"
    elif card_type == "cup":
        return "CUP"
    elif card_type == "rupay":
        return "RUPAY"
    else:
        return "UNKNOWN"

# Configurar la API de PayPal usando secretos
paypalrestsdk.configure({
    "mode": "live",  # Cambia a "live" para producción
    "client_id": st.secrets["PAYPAL_CLIENT_ID"],
    "client_secret": st.secrets["PAYPAL_CLIENT_SECRET"]
})

st.title("Verificación de Tarjetas de Crédito")
st.write("Ingrese los detalles de la tarjeta de crédito para verificarla.")

# Formulario para ingresar detalles de la tarjeta
card_number = st.text_input("Número de la Tarjeta de Crédito")
expire_month = st.selectbox("Mes de Vencimiento (MM)", [f"{i:02d}" for i in range(1, 13)])
current_year = 2024  # Año actual, cámbialo según sea necesario
expire_year = st.selectbox("Año de Vencimiento (YY)", [f"{i:02d}" for i in range(current_year % 100, (current_year + 10) % 100)])
cvv = st.text_input("CVV", type="password")

# Botón para verificar la tarjeta
button_style = """
    <style>
    .stButton button {
        background-color: green;
        color: white;
    }
    </style>
"""
st.markdown(button_style, unsafe_allow_html=True)

if st.button("Verificar Tarjeta"):
    if card_number and expire_month and expire_year and cvv:
        try:
            # Obtener información del banco emisor
            bank_info = get_bank_info(card_number)
            if bank_info:
                bank_name = bank_info.get('bank', {}).get('name', 'Desconocido')
                country = bank_info.get('country', 'Desconocido')
                card_type = bank_info.get('scheme', 'Desconocido').capitalize()
                country_flag = get_country_flag(country)
                
                # Mapear el tipo de tarjeta a un valor aceptado por PayPal
                card_type_paypal = map_card_type(card_type)
                
                if card_type_paypal == "UNKNOWN":
                    raise ValueError(f"Tipo de tarjeta no soportado: {card_type}")
                    
            else:
                bank_name = 'No disponible'
                country = 'No disponible'
                card_type = 'Desconocido'
                country_flag = ''
                card_type_paypal = 'UNKNOWN'

            # Crear una autorización de pago con PayPal
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
                            "last_name": "Doe",
                            "billing_address": {
                                "line1": "123 Main St",
                                "city": "San Jose",
                                "state": "CA",
                                "postal_code": "95131",
                                "country_code": country
                            }
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
                st.success("La tarjeta de crédito está aprobada.")
                st.write("#### Detalles de la Tarjeta:")
                st.write(f"- **Número de Tarjeta**: {card_number}")
                st.write(f"- **Fecha de Vencimiento**: {expire_month}/{expire_year}")
                st.write(f"- **CVV**: {cvv}")
                st.write(f"- **País**: {country} {country_flag}")
                st.write(f"- **Banco Emisor**: {bank_name}")
                st.write(f"- **Tipo**: {card_type}")

                # Anular la autorización para liberar los fondos
                authorization = paypalrestsdk.Authorization.find(authorization_id)
                if authorization.void():
                    st.info("La autorización ha sido anulada y los fondos han sido liberados.")
                else:
                    st.warning("No se pudo anular la autorización automáticamente. Por favor, revisa manualmente.")
            else:
                error_message = payment.error['message'] if 'message' in payment.error else 'Error desconocido'
                st.error(f"La tarjeta de crédito está declinada: {error_message}")
                st.error(f"Detalles del error: {payment.error}")

        except Exception as e:
            st.error(f"Error al procesar la tarjeta de crédito: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
