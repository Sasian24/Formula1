import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Quiniela F1", page_icon="🏎️")

# Título principal
st.title("🏆 Quiniela F1 - Temporada 2026")
st.subheader("Bienvenido al Paddock")

# Un poco de texto interactivo
piloto_fav = st.selectbox("Selecciona a tu piloto a seguir:", ["Checo Pérez", "Max Verstappen", "Franco Colapinto", "Charles Leclerc"])

if piloto_fav == "Checo Pérez":
    st.success("¡Excelente elección! El Ministro de Defensa en la casa. 🛡️🇲🇽")
else:
    st.info(f"Has seleccionado a {piloto_fav}. Veremos cómo le va en la pista.")

st.write("---")
st.write("¡Sistemas listos! Si ves esto, tu entorno de desarrollo en Mac está perfecto.")