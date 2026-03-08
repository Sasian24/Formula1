import streamlit as st
import gspread
from datetime import datetime, date, timedelta
import pandas as pd
import requests  

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Liga SasianGP 2026", page_icon="🏎️", layout="wide") 

# --- 2. CONEXIÓN A BASE DE DATOS ---
gc = gspread.service_account(filename="Config/credenciales.json")
sh = gc.open("SasianGP_DB")
tabla_quinielas = sh.worksheet("Quinielas")
tabla_jugadores = sh.worksheet("Jugadores")
tabla_resultados = sh.worksheet("Resultados") 
tabla_calendario = sh.worksheet("Calendario") 

# --- 3. LOGOS Y PILOTOS ---
url_logos = {
    "Red Bull Racing": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/red-bull.png",
    "Ferrari": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/ferrari.png",
    "Mercedes": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/mercedes.png",
    "McLaren": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/mclaren.png",
    "Aston Martin": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/aston-martin.png",
    "Alpine": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/alpine.png",
    "Williams": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/williams.png",
    "RB": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/rb.png",
    "Kick Sauber": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/sauber.png",
    "Haas": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/haas.png",
    "Cadillac": "https://www.google.com/s2/favicons?sz=128&domain=cadillac.com"
}

pilotos = sorted(["Checo Pérez", "Max Verstappen", "Charles Leclerc", "Lewis Hamilton", "Lando Norris", "Oscar Piastri", "George Russell", "Fernando Alonso", "Carlos Sainz", "Franco Colapinto", "Nico Hülkenberg", "Esteban Ocon", "Pierre Gasly", "Alex Albon", "Yuki Tsunoda", "Lance Stroll"])
carreras = ["1. GP de Australia (Marzo)", "2. GP de China (Marzo)", "3. GP de Japón (Marzo)", "4. GP de Bahréin (Abril)", "5. GP de Arabia Saudita (Abril)", "6. GP de Miami (Mayo)", "7. GP de Canadá (Mayo)", "8. GP de Mónaco (Junio)", "9. GP de España - Barcelona (Junio)", "10. GP de Austria (Junio)", "11. GP de Gran Bretaña (Julio)", "12. GP de Bélgica (Julio)", "13. GP de Hungría (Julio)", "14. GP de Países Bajos (Agosto)", "15. GP de Italia - Monza (Septiembre)", "16. GP de España - Madrid (Septiembre)", "17. GP de Azerbaiyán (Septiembre)", "18. GP de Singapur (Octubre)", "19. GP de Estados Unidos - Austin (Octubre)", "20. GP de México (Oct-Nov)", "21. GP de Brasil (Noviembre)", "22. GP de Las Vegas (Noviembre)", "23. GP de Qatar (Noviembre)", "24. GP de Abu Dhabi (Diciembre)"]

traductor_api = {"Verstappen": "Max Verstappen", "Perez": "Checo Pérez", "Leclerc": "Charles Leclerc", "Norris": "Lando Norris", "Sainz": "Carlos Sainz", "Hamilton": "Lewis Hamilton", "Russell": "George Russell", "Piastri": "Oscar Piastri", "Alonso": "Fernando Alonso", "Colapinto": "Franco Colapinto"}

# --- 4. GESTIÓN DE SESIÓN ---
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'auto_c1' not in st.session_state: st.session_state['auto_c1'] = None
if 'auto_c2' not in st.session_state: st.session_state['auto_c2'] = None
if 'auto_c3' not in st.session_state: st.session_state['auto_c3'] = None

# --- 5. INTERFAZ DE ACCESO ---
if st.session_state['usuario_activo'] is None:
    tab1, tab2, tab3 = st.tabs(["🔐 Acceso", "📝 Registrarse", "🆘 Olvidé mi Clave"])
    
    with tab1:
        st.title("Acceso - SasianGP")
        u = st.text_input("Alias de Piloto:", key="l_u")
        p = st.text_input("Contraseña de Telemetría:", type="password", key="l_p")
        if st.button("🏁 Arrancar Motores"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j.empty:
                df_j['Nombre'] = df_j['Nombre'].astype(str).str.strip()
                df_j['Password'] = df_j['Password'].astype(str).str.strip()
                if not df_j[(df_j['Nombre'] == u.strip()) & (df_j['Password'] == p.strip())].empty:
                    st.session_state['usuario_activo'] = u.strip()
                    st.rerun()
                else: st.error("❌ Acceso Denegado.")

    with tab2:
        st.title("Firma con la Escudería")
        nu = st.text_input("Alias de Piloto:", key="r_u")
        np = st.text_input("Contraseña:", type="password", key="r_p")
        esc = st.selectbox("Escudería:", list(url_logos.keys()), key="r_e")
        if st.button("✍️ Firmar Contrato"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            existentes = df_j['Nombre'].astype(str).str.strip().tolist() if not df_j.empty else []
            if not nu or not np: st.warning("⚠️ Llena todos los campos.")
            elif nu.strip() in existentes: st.error("❌ Alias ya ocupado.")
            else:
                ahora_mx = datetime.utcnow() - timedelta(hours=6)
                fila = [ahora_mx.strftime("%Y-%m-%d %H:%M"), nu.strip(), np.strip(), "", "", "", "", "", esc]
                tabla_jugadores.append_row(fila)
                st.success(f"✅ ¡Bienvenido {nu}! Ve a 'Acceso'.")

    with tab3:
        st.title("Recuperar Telemetría")
        uo = st.text_input("Tu Alias de Piloto:", key="f_u")
        if st.button("🔍 Buscar en el Paddock"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j.empty:
                match = df_j[df_j['Nombre'].astype(str).str.strip() == uo.strip()]
                if not match.empty: st.success(f"🔑 Tu clave es: **{match.iloc[0]['Password']}**")
                else: st.error("❓ Piloto no encontrado.")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    es_admin = st.session_state['usuario_activo'] == "Sasian"

    with st.sidebar:
        st.markdown(f"### 🏎️ Pits: {st.session_state['usuario_activo']}")
        opciones = ["📝 Hacer Apuesta", "🏆 El Paddock"]
        if es_admin: opciones.append("👑 Admin FIA")
        opciones.append("📖 Reglamento Oficial")
        menu = st.radio("Navegación", opciones)
        st.write("---")
        if st.button("🚪 Salir de Pits"):
            st.session_state['usuario_activo'] = None
            st.rerun()

    st.markdown("""<div style="text-align: center; background: #1e1e1e; padding: 10px; border-radius: 12px; border-bottom: 4px solid #E10600;"><span style="font-family: Impact; font-size: 3rem; color: #E10600; font-style: italic;">F1 SasianGP</span></div>""", unsafe_allow_html=True)

    if menu == "📝 Hacer Apuesta":
        st.subheader("Tu Pronóstico Oficial")
        df_cal = pd.DataFrame(tabla_calendario.get_all_records())
        gp_sel = st.selectbox("🌎 Selecciona Gran Premio:", carreras, index=None, placeholder="Elige un Gran Premio...")
        
        if not gp_sel:
            st.info("👆 Selecciona un Gran Premio para abrir los pits.")
        else:
            bq, bc = True, True 
            f = df_cal[df_cal['Carrera'] == gp_sel]
            if not f.empty:
                ahora = datetime.utcnow() - timedelta(hours=6)
                dt_q = pd.to_datetime(f.iloc[0]['Fecha_Qualy'], format="%H:%M %d-%m-%Y", errors='coerce')
                dt_c = pd.to_datetime(f.iloc[0]['Fecha_Carrera'], format="%H:%M %d-%m-%Y", errors='coerce')
                # Mantenemos el ajuste de 2 horas extras por hoy (+1h)
                if pd.notna(dt_q) and ahora < (dt_q + timedelta(hours=1)): bq = False
                if pd.notna(dt_c) and ahora < (dt_c
