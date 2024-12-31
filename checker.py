import streamlit as st
import paypalrestsdk
import requests

# Configuración de la API de PayPal
paypalrestsdk.configure({
    "mode": "live",  # Cambia a "live" para producción
    "client_id": st.secrets["PAYPAL_CLIENT_ID"],
    "client_secret": st.secrets["PAYPAL_CLIENT_SECRET"]
})

# Diccionario para almacenar el caché local de BIN
bin_cache = {}

# Función para obtener la información del banco emisor usando el número de tarjeta
def get_bank_info(card_number):
    bin_number = card_number[:6]
    # Verificar si ya está en caché
    if bin_number in bin_cache:
        return bin_cache[bin_number]
    
    try:
        # Usar BINList API gratuita
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            data = response.json()
            bin_cache[bin_number] = data  # Guardar en caché
            return data
        else:
            st.error(f"Error al consultar BIN: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con BINList API: {e}")
    
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
        "jcb": "JCB",
        "cup": "CUP"
    }
    return mapping.get(card_type, "null")

# Interfaz de usuario
st.title("Mondongo Verify TDC")
st.write("Ingrese los detalles de la tarjeta de crédito para verificarla.")

# Formulario para ingresar detalles de la tarjeta
card_number = st.text_input("Número de la Tarjeta de Crédito")
expire_month = st.selectbox("Mes de Vencimiento (MM)", [f"{i:02d}" for i in range(1, 13)])
current_year = 2024  # Año actual
expire_year = st.selectbox("Año de Vencimiento (YY)", [f"{i:02d}" for i in range(current_year % 100, (current_year + 10) % 100)])
cvv = st.text_input("CVV", type="password")

if st.button("Verificar Tarjeta"):
    if card_number and expire_month and expire_year and cvv:
        try:
            # Obtener información del banco emisor
            bank_info = get_bank_info(card_number)
            if bank_info:
                bank_name = bank_info.get('bank', {}).get('name', 'Desconocido')
                country = bank_info.get('country', {}).get('name', 'Desconocido')
                card_type = bank_info.get('scheme', 'Desconocido').capitalize()
            else:
                bank_name = 'No disponible'
                country = 'No disponible'
                card_type = 'Desconocido'

            # Mostrar los detalles de la tarjeta
            st.write("#### Detalles de la Tarjeta:")
            st.write(f"- **Banco Emisor**: {bank_name}")
            st.write(f"- **País**: {country}")
            st.write(f"- **Tipo de Tarjeta**: {card_type}")

            # Intentar realizar la autorización
            card_type_paypal = map_card_type(card_type)
            if card_type_paypal != "null":
                payment = paypalrestsdk.Payment({
                    "intent": "authorize",
                    "payer": {
                        "payment_method": "credit_card",
                        "funding_instruments": [{
                            "credit_card": {
                                "number": card_number,
                                "type": card_type_paypal,
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
                        "description": "Autorización de tarjeta de prueba"
                    }]
                })

                if payment.create():
                    st.success("La tarjeta de crédito está aprobada.")
                else:
                    error_message = payment.error.get('message', 'Error desconocido')
                    st.error(f"La tarjeta de crédito está declinada: {error_message}")
            else:
                st.warning(f"Tipo de tarjeta no soportado: {card_type}")

        except Exception as e:
            st.error(f"Error al procesar la tarjeta de crédito: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
