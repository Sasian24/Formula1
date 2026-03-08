import streamlit as st
import gspread
from datetime import datetime, timedelta
import pandas as pd
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SasianGP 2026", page_icon="🏎️", layout="wide")

# --- 2. CONEXIÓN A DB ---
gc = gspread.service_account(filename="Config/credenciales.json")
sh = gc.open("SasianGP_DB")
tabla_quinielas = sh.worksheet("Quinielas")
tabla_jugadores = sh.worksheet("Jugadores")
tabla_calendario = sh.worksheet("Calendario")

# --- 3. DATOS MAESTROS ---
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
    "Haas": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/haas.png"
}

pilotos = sorted(["Checo Pérez", "Max Verstappen", "Charles Leclerc", "Lewis Hamilton", "Lando Norris", "Oscar Piastri", "George Russell", "Fernando Alonso", "Carlos Sainz", "Franco Colapinto", "Nico Hülkenberg", "Esteban Ocon", "Pierre Gasly", "Alex Albon", "Yuki Tsunoda", "Lance Stroll"])
carreras = ["1. GP de Australia (Marzo)", "2. GP de China (Marzo)", "3. GP de Japón (Marzo)", "4. GP de Bahréin (Abril)", "5. GP de Arabia Saudita (Abril)", "6. GP de Miami (Mayo)", "7. GP de Canadá (Mayo)", "8. GP de Mónaco (Junio)", "9. GP de España - Barcelona (Junio)", "10. GP de Austria (Junio)", "11. GP de Gran Bretaña (Julio)", "12. GP de Bélgica (Julio)", "13. GP de Hungría (Julio)", "14. GP de Países Bajos (Agosto)", "15. GP de Italia - Monza (Septiembre)", "16. GP de España - Madrid (Septiembre)", "17. GP de Azerbaiyán (Septiembre)", "18. GP de Singapur (Octubre)", "19. GP de Estados Unidos - Austin (Octubre)", "20. GP de México (Oct-Nov)", "21. GP de Brasil (Noviembre)", "22. GP de Las Vegas (Noviembre)", "23. GP de Qatar (Noviembre)", "24. GP de Abu Dhabi (Diciembre)"]

traductor_api = {"Verstappen": "Max Verstappen", "Perez": "Checo Pérez", "Leclerc": "Charles Leclerc", "Norris": "Lando Norris", "Sainz": "Carlos Sainz", "Hamilton": "Lewis Hamilton", "Russell": "George Russell", "Piastri": "Oscar Piastri", "Alonso": "Fernando Alonso", "Colapinto": "Franco Colapinto"}

# --- 4. ESTADO DE SESIÓN ---
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'api_res' not in st.session_state: st.session_state['api_res'] = [None, None, None]

# --- 5. LÓGICA DE ACCESO ---
if st.session_state['usuario_activo'] is None:
    tab1, tab2 = st.tabs(["🔐 Entrar al Paddock", "📝 Registro de Escudería"])
    with tab1:
        u = st.text_input("Piloto:", key="u")
        p = st.text_input("Clave:", type="password", key="p")
        if st.button("🏁 Arrancar"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j.empty and not df_j[(df_j['Nombre'] == u.strip()) & (df_j['Password'] == p.strip())].empty:
                st.session_state['usuario_activo'] = u.strip()
                st.rerun()
            else: st.error("Acceso denegado.")
    with tab2:
        nu = st.text_input("Nuevo Piloto:", key="nu")
        np = st.text_input("Nueva Clave:", type="password", key="np")
        ne = st.selectbox("Escudería:", list(url_logos.keys()))
        if st.button("✍️ Firmar"):
            ahora = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M")
            tabla_jugadores.append_row([ahora, nu.strip(), np.strip(), "", "", "", "", "", ne])
            st.success("Registrado. Ve a 'Entrar'.")
else:
    # --- 6. INTERFAZ PRINCIPAL ---
    es_admin = st.session_state['usuario_activo'] == "Sasian"
    with st.sidebar:
        st.title(f"🏎️ {st.session_state['usuario_activo']}")
        menu = st.radio("Navegación", ["📝 Quiniela", "🏆 Paddock", "👑 Admin FIA", "📖 Reglamento"])
        if st.button("🚪 Salir"):
            st.session_state['usuario_activo'] = None
            st.rerun()

    if menu == "📝 Quiniela":
        st.header("Tus Pronósticos")
        df_cal = pd.DataFrame(tabla_calendario.get_all_records())
        gp = st.selectbox("Gran Premio:", carreras, index=None)
        if gp:
            f = df_cal[df_cal['Carrera'] == gp]
            bq, bc, ahora = True, True, (datetime.utcnow() - timedelta(hours=6))
            if not f.empty:
                dt_q = pd.to_datetime(f.iloc[0]['Fecha_Qualy'], format="%H:%M %d-%m-%Y")
                dt_c = pd.to_datetime(f.iloc[0]['Fecha_Carrera'], format="%H:%M %d-%m-%Y")
                if ahora < (dt_q + timedelta(hours=1)): bq = False
                if ahora < (dt_c + timedelta(hours=1)): bc = False
            
            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            ya_aposto = not df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp)].empty
            
            with st.form("f_q"):
                q1 = st.selectbox("Pole Position:", pilotos, disabled=bq or ya_aposto)
                g1 = st.selectbox("Ganador P1:", pilotos, disabled=bc or ya_aposto)
                g2 = st.selectbox("P2:", pilotos, disabled=bc or ya_aposto)
                g3 = st.selectbox("P3:", pilotos, disabled=bc or ya_aposto)
                vr = st.selectbox("Vuelta Rápida:", pilotos, disabled=bc or ya_aposto)
                ab = st.selectbox("Bono Salado (Abandono):", pilotos, disabled=bc or ya_aposto)
                if not ya_aposto and st.form_submit_button("🏁 Sellar"):
                    tabla_quinielas.append_row([ahora.strftime("%Y-%m-%d %H:%M"), st.session_state['usuario_activo'], gp, q1, "", "", g1, g2, g3, vr, ab, 0])
                    st.success("Apuesta sellada.")
                    st.rerun()
            if ya_aposto: st.warning("Pits cerrados para este GP.")

    elif menu == "🏆 Paddock":
        st.header("Tabla Mundial")
        df_q = pd.DataFrame(tabla_quinielas.get_all_records())
        if not df_q.empty:
            df_q['Puntos_Totales'] = pd.to_numeric(df_q['Puntos_Totales'], errors='coerce').fillna(0)
            res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False)
            st.dataframe(res, use_container_width=True, hide_index=True)

    elif menu == "📖 Reglamento":
        st.header("Reglamento SasianGP")
        st.success("🎯 Aciertos P1, P2, P3 y Pole: +3 pts cada uno. Vuelta Rápida: +2 pts.")
        st.warning("☠️ Bono Salado: +5 pts si aciertas el abandono, -2 pts si fallas.")
        st.info("⏱️ Cierre: 1 hora antes de la sesión.")

    elif menu == "👑 Admin FIA" and es_admin:
        st.header("Control de Carrera")
        if st.button("📡 Sincronizar API"):
            try:
                r = requests.get("https://api.jolpi.ca/ergast/f1/current/last/results.json").json()
                res = r['MRData']['RaceTable']['Races'][0]['Results']
                st.session_state['api_res'] = [traductor_api.get(res[i]['Driver']['familyName'], None) for i in range(3)]
                st.success("Telemetría lista.")
            except: st.error("Fallo de conexión API.")
        
        with st.form("fia"):
            sel_gp = st.selectbox("Calificar GP:", carreras)
            rq = st.selectbox("Pole Real:", pilotos)
            rv = st.selectbox("VR Real:", pilotos)
            ra = st.selectbox("Salado Real:", pilotos)
            c1, c2, c3 = st.columns(3)
            with c1: rg1 = st.selectbox("P1 Real:", pilotos, index=pilotos.index(st.session_state['api_res'][0]) if st.session_state['api_res'][0] in pilotos else 0)
            with c2: rg2 = st.selectbox("P2 Real:", pilotos, index=pilotos.index(st.session_state['api_res'][1]) if st.session_state['api_res'][1] in pilotos else 0)
            with c3: rg3 = st.selectbox("P3 Real:", pilotos, index=pilotos.index(st.session_state['api_res'][2]) if st.session_state['api_res'][2] in pilotos else 0)
            
            if st.form_submit_button("⚖️ Repartir Puntos"):
                aps = tabla_quinielas.get_all_records()
                for i, ap in enumerate(aps, start=2):
                    if ap['Carrera'] == sel_gp:
                        pts = 0
                        if ap['Qualy_P1'] == rq: pts += 3
                        if ap['Carrera_P1'] == rg1: pts += 3
                        if ap['Carrera_P2'] == rg2: pts += 3
                        if ap['Carrera_P3'] == rg3: pts += 3
                        if ap['Vuelta_Rapida'] == rv: pts += 2
                        if str(ap['Primer_Abandono']).strip():
                            if ap['Primer_Abandono'] == ra: pts += 5
                            else: pts -= 2
                        tabla_quinielas.update_cell(i, 12, pts)
                st.success("Puntos actualizados.")
