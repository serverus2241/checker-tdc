import streamlit as st
import paypalrestsdk
import requests

# Función para obtener la información del banco emisor usando el número de tarjeta
def get_bank_info(card_number):
    bin_number = card_number[:6]
    response = requests.get(f"https://lookup.binlist.net/{bin_number}")
    if response.status_code == 200:
        return response.json()
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
        "elo": "ELO",
        "hiper": "HIPER",
        "switch": "SWITCH",
        "jcb": "JCB",
        "hipercard": "HIPERCARD",
        "cup": "CUP",
        "rupay": "RUPAY"
    }
    return mapping.get(card_type, "null")

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

# Botón para verificar la tarjeta (inicialmente rojo)
button_style_red = """
    <style>
    .stButton button {
        background-color: red;
        color: white;
    }
    </style>
"""
st.markdown(button_style_red, unsafe_allow_html=True)

# Función para cambiar el color del botón a verde
def change_button_to_green():
    button_style_green = """
        <style>
        .stButton button {
            background-color: green;
            color: white;
        }
        </style>
    """
    st.markdown(button_style_green, unsafe_allow_html=True)

if st.button("Verificar Tarjeta"):
    if card_number and expire_month and expire_year and cvv:
        try:
            # Obtener información del banco emisor
            bank_info = get_bank_info(card_number)
            if bank_info:
                bank_name = bank_info.get('bank', {}).get('name', 'Desconocido')
                country = bank_info.get('country', 'Desconocido')
                card_type = bank_info.get('scheme', 'Desconocido').capitalize()
                
                # Mapear el tipo de tarjeta a un valor aceptado por PayPal
                card_type_paypal = map_card_type(card_type)
                if card_type_paypal == "null":
                    st.warning(f"Tipo de tarjeta no soportado: {card_type}")
                    
            else:
                bank_name = 'No disponible'
                country = 'No disponible'
                card_type = 'null'
                card_type_paypal = 'null'

            # Mostrar los detalles de la tarjeta antes de la autorización
            st.write("#### Detalles de la Tarjeta:")
            st.write(f"- **País**: {country}")
            st.write(f"- **Tipo**: {card_type if card_type_paypal != 'null' else 'null'}")
            st.write(f"- **Banco Emisor**: {bank_name}")

            # Intentar realizar la autorización solo si el tipo de tarjeta es soportado
            if card_type_paypal != "null":
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

                    # Anular la autorización para liberar los fondos
                    authorization = paypalrestsdk.Authorization.find(authorization_id)
                    if authorization.void():
                        st.info("La autorización ha sido anulada y los fondos han sido liberados.")
                    else:
                        st.warning("No se pudo anular la autorización automáticamente. Por favor, revisa manualmente.")
                    
                    change_button_to_green()
                else:
                    st.error(f"La tarjeta de crédito está declinada.")
        except Exception as e:
            st.error("Error al procesar la tarjeta de crédito.")
    else:
        st.warning("Por favor, complete todos los campos.")
