import streamlit as st
import paypalrestsdk
import pycountry
import requests

def get_country_flag(country_code):
    country = pycountry.countries.get(alpha_2=country_code)
    if country:
        # Convertir el código del país en un emoji de bandera
        return chr(127397 + ord(country.alpha_2[0])) + chr(127397 + ord(country.alpha_2[1]))
    return ""

def get_bank_info(card_number):
    bin_number = card_number[:6]
    response = requests.get(f"https://lookup.binlist.net/{bin_number}")
    if response.status_code == 200:
        return response.json()
    return None

# Configurar la API de PayPal usando secretos
paypalrestsdk.configure({
    "mode": "sandbox",  # Cambia a "live" para producción
    "client_id": st.secrets["PAYPAL_CLIENT_ID"],
    "client_secret": st.secrets["PAYPAL_CLIENT_SECRET"]
})

st.title("Mondongo Veryfy TDC V1.")
st.write("Ingrese los detalles de la tarjeta de crédito para verificarla.")

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
                country_flag = get_country_flag(country)
            else:
                bank_name = 'No disponible'
                country = 'No disponible'
                card_type = 'Desconocido'
                country_flag = ''

            st.success("La tarjeta de crédito está aprobada.")
            st.write(f"#### Detalles de la Tarjeta:")
            st.write(f"- **Tipo**: {card_type}")
            st.write(f"- **Banco Emisor**: {bank_name}")
            st.write(f"- **País**: {country} {country_flag}")

        except Exception as e:
            st.error(f"Error al procesar la tarjeta de crédito: {str(e)}")
    else:
        st.warning("Por favor, complete todos los campos.")
