import streamlit as st
import gspread
from datetime import datetime, date, timedelta
import pandas as pd
import requests  

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="Liga SasianGP 2026", page_icon="🏎️", layout="wide") 

gc = gspread.service_account(filename="Config/credenciales.json")
sh = gc.open("SasianGP_DB")
tabla_quinielas = sh.worksheet("Quinielas")
tabla_jugadores = sh.worksheet("Jugadores")
tabla_resultados = sh.worksheet("Resultados") 
tabla_calendario = sh.worksheet("Calendario") 

# --- 2. LOGOS Y CATÁLOGOS ---
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
    "Cadillac": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Cadillac_Logo.svg/320px-Cadillac_Logo.svg.png"
}

pilotos = sorted(["Checo Pérez", "Max Verstappen", "Charles Leclerc", "Lewis Hamilton", "Lando Norris", "Oscar Piastri", "George Russell", "Fernando Alonso", "Carlos Sainz", "Franco Colapinto", "Nico Hülkenberg", "Esteban Ocon", "Pierre Gasly", "Alex Albon", "Yuki Tsunoda", "Lance Stroll"])
carreras = [
    "1. GP de Australia (Marzo)", "2. GP de China (Marzo)", "3. GP de Japón (Marzo)", 
    "4. GP de Bahréin (Abril)", "5. GP de Arabia Saudita (Abril)", "6. GP de Miami (Mayo)", 
    "7. GP de Canadá (Mayo)", "8. GP de Mónaco (Junio)", "9. GP de España - Barcelona (Junio)"
]

traductor_api = {
    "Verstappen": "Max Verstappen", "Perez": "Checo Pérez", "Leclerc": "Charles Leclerc",
    "Norris": "Lando Norris", "Sainz": "Carlos Sainz", "Hamilton": "Lewis Hamilton",
    "Russell": "George Russell", "Piastri": "Oscar Piastri", "Alonso": "Fernando Alonso",
    "Colapinto": "Franco Colapinto"
}

# --- 3. GESTIÓN DE SESIÓN ---
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'auto_c1' not in st.session_state: st.session_state['auto_c1'] = None
if 'auto_c2' not in st.session_state: st.session_state['auto_c2'] = None
if 'auto_c3' not in st.session_state: st.session_state['auto_c3'] = None

# --- 4. ACCESO ---
if st.session_state['usuario_activo'] is None:
    st.title("🔐 Acceso - SasianGP")
    u = st.text_input("Alias de Piloto:")
    p = st.text_input("Contraseña de Telemetría:", type="password")
    if st.button("🏁 Arrancar Motores"):
        df_j = pd.DataFrame(tabla_jugadores.get_all_records())
        if not df_j.empty:
            df_j['Nombre'] = df_j['Nombre'].astype(str).str.strip()
            df_j['Password'] = df_j['Password'].astype(str).str.strip()
            if not df_j[(df_j['Nombre'] == u.strip()) & (df_j['Password'] == p.strip())].empty:
                st.session_state['usuario_activo'] = u.strip()
                st.rerun()
            else: st.error("❌ Acceso Denegado. Piloto no registrado o contraseña inválida.")

# --- 5. APLICACIÓN PRINCIPAL ---
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

    # BANNER PREMIUM SASIAN
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 12px; margin-bottom: 25px; border-bottom: 4px solid #E10600; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
            <span style="font-size: 2.5rem;">🏁</span>
            <div style="text-align: center;">
                <span style="font-family: Impact; font-size: 3.5rem; font-style: italic; color: #E10600; letter-spacing: -1px;">F1<sup style="font-size: 1.2rem; color: #fff;">&reg; Sasian</sup></span>
            </div>
            <span style="font-size: 2.5rem;">🏁</span>
        </div>
    """, unsafe_allow_html=True)

    # --- PANTALLA: APUESTAS ---
    if menu == "📝 Hacer Apuesta":
        st.subheader("Tu Pronóstico Oficial")
        df_cal = pd.DataFrame(tabla_calendario.get_all_records())
        gp_sel = st.selectbox("🌎 Selecciona Gran Premio:", carreras, index=None)
        
        bq, bc = False, False
        f_qualy_str, f_carrera_str = "Por definir", "Por definir"
        
        if gp_sel and not df_cal.empty:
            f = df_cal[df_cal['Carrera'] == gp_sel]
            if not f.empty:
                f_q = str(f.iloc[0]['Fecha_Qualy'])
                f_c = str(f.iloc[0]['Fecha_Carrera'])
                
                # FORZAMOS EL FORMATO 24 HORAS: HH:MM DD-MM-YYYY
                try:
                    dt_q = pd.to_datetime(f_q)
                    dt_c = pd.to_datetime(f_c)
                    f_qualy_str = dt_q.strftime("%H:%M  %d-%m-%Y")
                    f_carrera_str = dt_c.strftime("%H:%M  %d-%m-%Y")
                except:
                    f_qualy_str = f_q
                    f_carrera_str = f_c
                
                st.info(f"⏱️ **Límites de Apuesta (24 hrs):** \n* **Qualy:** {f_qualy_str} \n* **Carrera:** {f_carrera_str}")
                
                ahora = datetime.now()
                try:
                    if ahora > (dt_q - timedelta(hours=1)): bq = True
                    if ahora > (dt_c - timedelta(hours=1)): bc = True
                except: pass

        with st.form("apuesta_form"):
            st.markdown(f"### ⏱️ Calificación (Inicia: {f_qualy_str})")
            c1, c2, c3 = st.columns(3)
            with c1: q1 = st.selectbox("PP1 (Pole):", pilotos, index=None, disabled=bq)
            with c2: q2 = st.selectbox("PP2:", pilotos, index=None, disabled=bq)
            with c3: q3 = st.selectbox("PP3:", pilotos, index=None, disabled=bq)
            
            st.write("---")
            
            st.markdown(f"### 🏁 Carrera (Inicia: {f_carrera_str})")
            c4, c5, c6 = st.columns(3)
            with c4: g1 = st.selectbox("Ganador (P1):", pilotos, index=None, disabled=bc)
            with c5: g2 = st.selectbox("P2:", pilotos, index=None, disabled=bc)
            with c6: g3 = st.selectbox("P3:", pilotos, index=None, disabled=bc)
            
            st.write("---")
            
            st.markdown("### 🎲 Bonos Especiales")
            b1, b2 = st.columns(2)
            with b1: vr = st.selectbox("🚀 Vuelta Rápida:", pilotos, index=None, disabled=bc)
            with b2: ab = st.selectbox("💥 Primer Abandono (Opcional):", pilotos, index=None, disabled=bc)
            
            if st.form_submit_button("🏎️ Enviar Pronóstico a Telemetría", disabled=(bq and bc)):
                if not gp_sel: st.error("⚠️ Llantas frías. Debes seleccionar una carrera.")
                else:
                    v_ab = "🔒 CERRADO" if bc else (ab if ab else "")
                    fila = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, g1, g2, g3, vr, v_ab, 0]
                    tabla_quinielas.append_row(fila)
                    st.success("✅ ¡Apuesta sellada y registrada! Suerte, la vas a necesitar.")
                    st.balloons()

    # --- PANTALLA: EL PADDOCK ---
    elif menu == "🏆 El Paddock":
        st.subheader("Clasificación Mundial del Campeonato")
        datos_q = tabla_quinielas.get_all_records()
        df_j = pd.DataFrame(tabla_jugadores.get_all_records())
        
        if datos_q:
            df_a = pd.DataFrame(datos_q)
            df_a['Puntos_Totales'] = pd.to_numeric(df_a['Puntos_Totales'], errors='coerce').fillna(0)
            
            # BLINDAJE ANTI-ESPACIOS INVISIBLES
            df_a['Jugador'] = df_a['Jugador'].astype(str).str.strip()
            if not df_j.empty:
                # Limpiamos todos los nombres de columnas para que siempre encuentre 'Escuderia_Favorita'
                df_j.columns = df_j.columns.str.strip() 
                df_j['Nombre'] = df_j['Nombre'].astype(str).str.strip()
                col_e = 'Escuderia_Favorita' if 'Escuderia_Favorita' in df_j.columns else 'Escudería'
                if col_e in df_j.columns:
                    df_j[col_e] = df_j[col_e].astype(str).str.strip()
            
            res = df_a.groupby('Jugador')['Puntos_Totales'].sum().reset_index()
            res = res.sort_values(by='Puntos_Totales', ascending=False).reset_index(drop=True)
            
            if not df_j.empty and col_e in df_j.columns:
                res = res.merge(df_j[['Nombre', col_e]], left_on='Jugador', right_on='Nombre', how='left')
                res['🛡️'] = res[col_e].map(url_logos).fillna(url_logos["Cadillac"])
            else:
                res['🛡️'] = url_logos["Cadillac"]
            
            res.index = range(1, len(res) + 1)
            st.dataframe(
                res[['🛡️', 'Jugador', 'Puntos_Totales']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "🛡️": st.column_config.ImageColumn("", width="small"),
                    "Jugador": st.column_config.TextColumn("PILOTO"),
                    "Puntos_Totales": st.column_config.NumberColumn("PTS ⚡", format="%d")
                }
            )
        else:
            st.info("🚦 El semáforo sigue en rojo. Aún no hay pronósticos registrados.")

    # --- PANTALLA: REGLAMENTO OFICIAL ---
    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("""
        El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. 
        * **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista el sábado.
        * **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde del domingo.
        * **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos en esa sesión. Ni mandándole un WhatsApp a Sasian se te va a abrir el sistema.
        """)
        
        st.markdown("### 🎯 ARTÍCULO 2: El Podio (Precisión Absoluta)")
        st.success("""
        Aquí no hay premios de consolación por "casi" atinarle. O le das a la posición exacta o tienes cero. Si pones a Checo Pérez en P1 y llega en P2, **no sumas nada**.
        * 🥇 **Ganador de la Carrera (P1):** Te otorga **+3 Puntos**.
        * 🥈 **Segundo Lugar (P2):** Te otorga **+3 Puntos**.
        * 🥉 **Tercer Lugar (P3):** Te otorga **+3 Puntos**.
        * ⏱️ **Pole Position (Qualy P1):** Te otorga **+3 Puntos** (Solo cuenta el PP1, P2 y P3 de la Qualy por ahora son de desempate/honor).
        * 🚀 **Vuelta Rápida:** Te otorga **+2 Puntos** si adivinas quién hace el giro más rápido durante la carrera del domingo.
        """)

        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("""
        Para los morbosos que disfrutan ver fibra de carbono volando. Esta apuesta es **OPCIONAL**. Si decides maldecir a un piloto y pronosticas que será el **Primer Abandono** de la carrera:
        * ✅ **Si Acertaste:** Si tu piloto choca, se le funde el motor o abandona primero que nadie, eres un genio del mal y te llevas **+5 Puntos** directos.
        * ❌ **Si Fallaste:** Si tu piloto sobrevive la carrera o si alguien más abandona antes que él, la FIA te castiga con **-2 Puntos** sobre el total de tu carrera por andar de salado. 
        * 🛡️ **Tip de cobardes:** Dejar el espacio en blanco o decir "Nadie" es totalmente válido y te salva de los puntos negativos. Cero riesgo, cero ganancia.
        """)

        st.markdown("### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
        st.error("Los resultados son inyectados directamente por la telemetría oficial de la **API de la Fórmula 1** y validados por el mismísimo **Sasian**. Si la app dice que sacaste 0, sacaste 0. Cualquier queja, reclamo o berrinche será ignorado olímpicamente. La decisión final es absoluta e inapelable.")

    # --- PANTALLA: ADMIN FIA ---
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
