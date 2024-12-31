import streamlit as st
import paypalrestsdk

# Configurar la API de PayPal
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

# Nuevos campos para ingresar los detalles del titular de la tarjeta
first_name = st.text_input("Nombre del Titular")
last_name = st.text_input("Apellido del Titular")
address_line1 = st.text_input("Dirección de Facturación")
city = st.text_input("Ciudad")
state = st.text_input("Estado/Provincia")
postal_code = st.text_input("Código Postal")
country_code = st.text_input("Código del País (por ejemplo, US)")

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
    if card_number and expire_month and expire_year and cvv and first_name and last_name and address_line1 and city and state and postal_code and country_code:
        try:
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
                            "expire_year": "20" + expire_year,
                            "cvv2": cvv,
                            "first_name": first_name,
                            "last_name": last_name,
                            "billing_address": {
                                "line1": address_line1,
                                "city": city,
                                "state": state,
                                "postal_code": postal_code,
                                "country_code": country_code
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
                st.success(f"La tarjeta de crédito está aprobada.\n"
                           f"Tipo: {payment.payer.funding_instruments[0].credit_card.type.upper()}\n"
                           f"País: {payment.payer.funding_instruments[0].credit_card.billing_address['country_code']}\n"
                           f"Código Postal: {payment.payer.funding_instruments[0].credit_card.billing_address['postal_code']}\n"
                           f"Nombre del Titular: {payment.payer.funding_instruments[0].credit_card.first_name} {payment.payer.funding_instruments[0].credit_card.last_name}\n"
                           f"Fecha de Vencimiento: {payment.payer.funding_instruments[0].credit_card.expire_month}/{payment.payer.funding_instruments[0].credit_card.expire_year}")

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

            change_button_to_green()
        except Exception as e:
            st.error(f"Error al procesar la tarjeta de crédito: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
