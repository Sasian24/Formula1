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
        nu = st.text_input("Crea tu Alias de Piloto:", key="r_u")
        np = st.text_input("Crea tu Contraseña:", type="password", key="r_p")
        esc = st.selectbox("Selecciona tu Escudería:", list(url_logos.keys()), key="r_e")
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
                # Mantenemos el ajuste temporal de 2 horas (+1h en lugar de -1h)
                if pd.notna(dt_q) and ahora < (dt_q + timedelta(hours=1)): bq = False
                if pd.notna(dt_c) and ahora < (dt_c + timedelta(hours=1)): bc = False

            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            ya_aposto, ap_p = False, {}
            if not df_q.empty:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
                if not filtro.empty:
                    ya_aposto, ap_p = True, filtro.iloc[-1].to_dict()
                    st.info("💡 Ya tienes una quiniela registrada (Regla de Parque Cerrado). Aquí están tus pronósticos:")

            def get_idx(campo):
                return pilotos.index(ap_p[campo]) if ya_aposto and ap_p.get(campo) in pilotos else None

            with st.form("apuesta_form"):
                st.markdown("### ⏱️ Calificación")
                q1 = st.selectbox("PP1 (Pole):", pilotos, index=get_idx('Qualy_P1'), disabled=bq or ya_aposto)
                st.write("---")
                st.markdown("### 🏁 Carrera")
                c4, c5, c6 = st.columns(3)
                with c4: g1 = st.selectbox("Ganador (P1):", pilotos, index=get_idx('Carrera_P1'), disabled=bc or ya_aposto)
                with c5: g2 = st.selectbox("P2:", pilotos, index=get_idx('Carrera_P2'), disabled=bc or ya_aposto)
                with c6: g3 = st.selectbox("P3:", pilotos, index=get_idx('Carrera_P3'), disabled=bc or ya_aposto)
                st.write("---")
                st.markdown("### 🎲 Bonos Especiales")
                b1, b2 = st.columns(2)
                with b1: vr = st.selectbox("🚀 Vuelta Rápida:", pilotos, index=get_idx('Vuelta_Rapida'), disabled=bc or ya_aposto)
                with b2: ab = st.selectbox("💥 Primer Abandono (Opcional):", pilotos, index=get_idx('Primer_Abandono'), disabled=bc or ya_aposto)
                
                if not ya_aposto:
                    if st.form_submit_button("🏎️ Sellar Apuesta"):
                        v_ab = "🔒 CERRADO" if bc else (ab if ab else "")
                        fila = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, "", "", g1, g2, g3, vr, v_ab, 0]
                        tabla_quinielas.append_row(fila)
                        st.success("✅ ¡Apuesta sellada!")
                        st.rerun()
                else: st.form_submit_button("🔒 Apuesta en Parque Cerrado", disabled=True)

    elif menu == "🏆 El Paddock":
        st.subheader("Clasificación Mundial del Campeonato")
        dq = tabla_quinielas.get_all_records()
        df_j = pd.DataFrame(tabla_jugadores.get_all_records())
        if dq:
            df = pd.DataFrame(dq)
            df['Puntos_Totales'] = pd.to_numeric(df['Puntos_Totales'], errors='coerce').fillna(0)
            res = df.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False).reset_index(drop=True)
            if not df_j.empty:
                res = res.merge(df_j[['Nombre', 'Escuderia_Favorita']], left_on='Jugador', right_on='Nombre', how='left')
                res['🛡️'] = res['Escuderia_Favorita'].map(url_logos).fillna(url_logos["Cadillac"])
            st.dataframe(res[['🛡️', 'Jugador', 'Puntos_Totales']], use_container_width=True, hide_index=True, column_config={"🛡️": st.column_config.ImageColumn("")})

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \\n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos. Ni mandándole WhatsApp a Sasian se abre.")
        st.markdown("### ### 🎯 ARTÍCULO 2: El Podio (Precisión Absoluta)")
        st.success("Aquí no hay premios de consolación por 'casi' atinarle. O le das a la posición exacta o tienes cero.\\n* 🥇 **Ganador (P1):** +3 Puntos.\\n* 🥈 **Segundo (P2):** +3 Puntos.\\n* 🥉 **Tercer (P3):** +3 Puntos.\\n* ⏱️ **Pole Position (Qualy P1):** +3 Puntos.\\n* 🚀 **Vuelta Rápida:** +2 Puntos si adivinas quién hace el giro más rápido el domingo.")
        st.markdown("### ### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("Esta apuesta es **OPCIONAL**.\\n* ✅ **Si Acertaste:** Si tu piloto es el primero en abandonar, eres un genio del mal y te llevas **+5 Puntos** directos.\\n* ❌ **Si Fallaste:** Si sobrevive o alguien más abandona antes, te castigamos con **-2 Puntos**.\\n* 🛡️ **Tip:** Dejar el espacio en blanco es totalmente válido y te salva de perder puntos.")
        st.markdown("### ### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
        st.error("Los resultados son inyectados directamente por la telemetría oficial de la API y validados por el mismísimo **Sasian**. La decisión final es absoluta e inapelable.")

    elif menu == "👑 Admin FIA":
        st.subheader("Control del Director de Carrera")
        if st.button("⚡ Extraer Telemetría API"):
            try:
                r = requests.get("https://api.jolpi.ca/ergast/f1/current/last/results.json").json()
                res_api = r['MRData']['RaceTable']['Races'][0]['Results']
                st.session_state['auto_c1'] = traductor_api.get(res_api[0]['Driver']['familyName'], None)
                st.session_state['auto_c2'] = traductor_api.get(res_api[1]['Driver']['familyName'], None)
                st.session_state['auto_c3'] = traductor_api.get(res_api[2]['Driver']['familyName'], None)
                st.success("✅ Datos descargados con éxito.")
            except: st.error("❌ Error de comunicación.")

        with st.form("fia_form"):
            sel_car = st.selectbox("Gran Premio a Dictaminar:", carreras)
            idx1 = pilotos.index(st.session_state['auto_c1']) if st.session_state['auto_c1'] in pilotos else None
            idx2 = pilotos.index(st.session_state['auto_c2']) if st.session_state['auto_c2'] in pilotos else None
            idx3 = pilotos.index(st.session_state['auto_c3']) if st.session_state['auto_c3'] in pilotos else None
            c1, c2, c3 = st.columns(3)
            with c1: rq1 = st.selectbox("Pole Real:", pilotos)
            with c2: rvr = st.selectbox("VR Real:", pilotos)
            with c3: rab = st.selectbox("Salado Real:", pilotos)
            st.write("---")
            c4, c5, c6 = st.columns(3)
            with c4: rg1 = st.selectbox("P1 Carrera:", pilotos, index=idx1)
            with c5: rg2 = st.selectbox("P2 Carrera:", pilotos, index=idx2)
            with c6: rg3 = st.selectbox("P3 Carrera:", pilotos, index=idx3)

            if st.form_submit_button("⚖️ Repartir Puntos"):
                tabla_resultados.append_row([sel_car, rq1, "", "", rg1, rg2, rg3, rvr, rab])
                aps = tabla_quinielas.get_all_records()
                for i, ap in enumerate(aps, start=2):
                    if ap['Carrera'] == sel_car:
                        p = 0
                        if ap['Carrera_P1'] == rg1: p += 3
                        if ap['Carrera_P2'] == rg2: p += 3
                        if ap['Carrera_P3'] == rg3: p += 3
                        if ap['Qualy_P1'] == rq1: p += 3
                        if ap['Vuelta_Rapida'] == rvr: p += 2
                        s_ap = str(ap.get('Primer_Abandono', '')).strip()
                        if s_ap != "" and s_ap != "🔒 CERRADO":
                            if s_ap == rab: p += 5
                            else: p -= 2
                        tabla_quinielas.update_cell(i, 12, p)
                st.success("🏆 ¡Puntos actualizados en la base de datos!")
