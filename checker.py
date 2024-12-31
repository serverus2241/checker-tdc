import streamlit as st
import paypalrestsdk
import pycountry

def get_country_flag(country_code):
    country = pycountry.countries.get(alpha_2=country_code)
    if country:
        # Convert country code to flag emoji
        return chr(127397 + ord(country.alpha_2[0])) + chr(127397 + ord(country.alpha_2[1]))
    return ""

# Configurar la API de PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Cambia a "live" para producción
    "client_id": st.secrets["PAYPAL_CLIENT_ID"],
    "client_secret": st.secrets["PAYPAL_CLIENT_SECRET"]
})

st.title("Mondongo Verify TDC")
st.write("Ingrese los detalles de la tarjeta de crédito para verificarla.")

# Formulario para ingresar detalles de la tarjeta
card_number = st.text_input("Número de la Tarjeta de Crédito")

# Menú desplegable para seleccionar el mes de vencimiento
expire_month = st.selectbox("Mes de Vencimiento (MM)", [f"{i:02d}" for i in range(1, 13)])

# Menú desplegable para seleccionar el año de vencimiento
current_year = 2024  # Año actual, cámbialo según sea necesario
expire_year = st.selectbox("Año de Vencimiento (YY)", [f"{i:02d}" for i in range(current_year % 100, (current_year + 10) % 100)])

cvv = st.text_input("CVV", type="password")

# Botón para verificar la tarjeta
if st.button("Verificar Tarjeta"):
    if card_number and expire_month and expire_year and cvv:
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
                            "first_name": "John",
                            "last_name": "Doe",
                            "billing_address": {
                                "line1": "123 Main St",
                                "city": "San Jose",
                                "state": "CA",
                                "postal_code": "95131",
                                "country_code": "US"
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

            card_info = payment.payer.funding_instruments[0].credit_card
            card_type = card_info.type
            country = card_info.billing_address['country_code']
            postal_code = card_info.billing_address['postal_code']
            first_name = card_info.first_name
            last_name = card_info.last_name
            expire_month = card_info.expire_month
            expire_year = card_info.expire_year

            country_flag = get_country_flag(country)

            # Intentar realizar la autorización
            if payment.create():
                authorization_id = payment.transactions[0].related_resources[0].authorization.id

                st.success(f"La tarjeta de crédito está aprobada.\n"
                           f"Tipo: {card_type.upper()}\n"
                           f"País: {country} {country_flag}\n"
                           f"Código Postal: {postal_code}\n"
                           f"Nombre del Titular: {first_name} {last_name}\n"
                           f"Fecha de Vencimiento: {expire_month}/{expire_year}")

                # Anular la autorización para liberar los fondos
                authorization = paypalrestsdk.Authorization.find(authorization_id)
                if authorization.void():
                    st.info("La autorización ha sido anulada y los fondos han sido liberados.")
                else:
                    st.warning("No se pudo anular la autorización automáticamente. Por favor, revisa manualmente.")
            else:
                error_message = payment.error['message'] if 'message' in payment.error else 'Error desconocido'
                st.error(f"La tarjeta de crédito está declinada: {error_message}\n"
                         f"Tipo: {card_type.upper()}\n"
                         f"País: {country} {country_flag}\n"
                         f"Código Postal: {postal_code}\n"
                         f"Nombre del Titular: {first_name} {last_name}\n"
                         f"Fecha de Vencimiento: {expire_month}/{expire_year}")
        except Exception as e:
            st.error(f"Error al procesar la tarjeta de crédito: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
