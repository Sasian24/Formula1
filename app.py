import streamlit as st
import gspread
from datetime import datetime, timedelta
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
    "Racing Bulls": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/rb.png",
    "Audi": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/sauber.png",
    "Haas": "https://raw.githubusercontent.com/f1db/f1db-images/main/images/teams/haas.png",
    "Cadillac": "https://www.google.com/s2/favicons?sz=128&domain=cadillac.com"
}

pilotos = sorted([
    "Checo Pérez", "Max Verstappen", "Charles Leclerc", "Lewis Hamilton", 
    "Lando Norris", "Oscar Piastri", "George Russell", "Fernando Alonso", 
    "Carlos Sainz", "Franco Colapinto", "Nico Hülkenberg", "Esteban Ocon", 
    "Pierre Gasly", "Alex Albon", "Lance Stroll", "Valtteri Bottas",
    "Arvid Lindblad", "Isack Hadjar", "Kimi Antonelli", "Oliver Bearman", 
    "Liam Lawson", "Gabriel Bortoleto"
])

carreras = ["1. GP de Australia (Marzo)", "2. GP de China (Marzo)", "3. GP de Japón (Marzo)", "4. GP de Bahréin (Abril)", "5. GP de Arabia Saudita (Abril)", "6. GP de Miami (Mayo)", "7. GP de Canadá (Mayo)", "8. GP de Mónaco (Junio)", "9. GP de España - Barcelona (Junio)", "10. GP de Austria (Junio)", "11. GP de Gran Bretaña (Julio)", "12. GP de Bélgica (Julio)", "13. GP de Hungría (Julio)", "14. GP de Países Bajos (Agosto)", "15. GP de Italia - Monza (Septiembre)", "16. GP de España - Madrid (Septiembre)", "17. GP de Azerbaiyán (Septiembre)", "18. GP de Singapur (Octubre)", "19. GP de Estados Unidos - Austin (Octubre)", "20. GP de México (Oct-Nov)", "21. GP de Brasil (Noviembre)", "22. GP de Las Vegas (Noviembre)", "23. GP de Qatar (Noviembre)", "24. GP de Abu Dhabi (Diciembre)"]

traductor_api = {
    "Verstappen": "Max Verstappen", "Perez": "Checo Pérez", "Leclerc": "Charles Leclerc", 
    "Norris": "Lando Norris", "Sainz": "Carlos Sainz", "Hamilton": "Lewis Hamilton", 
    "Russell": "George Russell", "Piastri": "Oscar Piastri", "Alonso": "Fernando Alonso", 
    "Colapinto": "Franco Colapinto", "Lindblad": "Arvid Lindblad", "Hadjar": "Isack Hadjar",
    "Antonelli": "Kimi Antonelli", "Bearman": "Oliver Bearman", "Lawson": "Liam Lawson",
    "Bortoleto": "Gabriel Bortoleto", "Hülkenberg": "Nico Hülkenberg", "Hulkenberg": "Nico Hülkenberg",
    "Ocon": "Esteban Ocon", "Gasly": "Pierre Gasly", "Albon": "Alex Albon", 
    "Stroll": "Lance Stroll", "Bottas": "Valtteri Bottas"
}

# --- 4. GESTIÓN DE SESIÓN ---
if 'usuario_activo' not in st.session_state: 
    st.session_state['usuario_activo'] = None
if 'auto_c1' not in st.session_state: 
    st.session_state['auto_c1'] = None
if 'auto_c2' not in st.session_state: 
    st.session_state['auto_c2'] = None
if 'auto_c3' not in st.session_state: 
    st.session_state['auto_c3'] = None

# --- 5. INTERFAZ DE ACCESO (3 PESTAÑAS) ---
if st.session_state['usuario_activo'] is None:
    tab1, tab2, tab3 = st.tabs(["🔐 Acceso", "📝 Registrarse", "🆘 Olvidé mi Clave"])
    
    with tab1:
        st.title("Acceso - SasianGP")
        u = st.text_input("Alias de Piloto:", key="login_u")
        p = st.text_input("Contraseña de Telemetría:", type="password", key="login_p")
        if st.button("🏁 Arrancar Motores"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j.empty:
                df_j['Nombre'] = df_j['Nombre'].astype(str).str.strip()
                df_j['Password'] = df_j['Password'].astype(str).str.strip()
                if not df_j[(df_j['Nombre'] == u.strip()) & (df_j['Password'] == p.strip())].empty:
                    st.session_state['usuario_activo'] = u.strip()
                    st.rerun()
                else: 
                    st.error("❌ Acceso Denegado. Piloto no registrado o clave incorrecta.")

    with tab2:
            st.title("Firma con la Escudería")
            st.markdown("Llena tu perfil para unirte al campeonato.")
            
            nu = st.text_input("Crea tu Alias de Piloto * (Obligatorio):", key="reg_u")
            np = st.text_input("Crea tu Contraseña * (Obligatorio):", type="password", key="reg_p")
            
            c1, c2 = st.columns(2)
            with c1:
                wp = st.text_input("📱 WhatsApp (Opcional):", key="reg_wp")
                cumple = st.date_input("🎂 Fecha de Nacimiento:", value=None, min_value=datetime(1940, 1, 1), max_value=datetime.today())
            with c2:
                mail = st.text_input("📧 Correo Electrónico (Opcional):", key="reg_m")
                piloto_fav = st.selectbox("🏎️ Piloto Favorito:", pilotos, index=None, placeholder="Elige a tu ídolo...")
    
            esc = st.selectbox("🛡️ Selecciona tu Escudería * (Obligatorio):", list(url_logos.keys()), key="reg_e")
            
            if st.button("✍️ Firmar Contrato"):
                df_j = pd.DataFrame(tabla_jugadores.get_all_records())
                existentes = df_j['Nombre'].astype(str).str.strip().tolist() if not df_j.empty else []
                
                # Validación: Solo Alias, Pass y Escudería son estrictamente obligatorios
                if not nu or not np or not esc: 
                    st.warning("⚠️ Debes llenar al menos el Alias, Contraseña y Escudería.")
                elif nu.strip() in existentes: 
                    st.error("❌ Ese Alias ya está ocupado en el Paddock.")
                else:
                    ahora_mx = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
                    # Formatear fecha y piloto por si los dejaron vacíos
                    fecha_cumple = cumple.strftime("%Y-%m-%d") if cumple else ""
                    piloto_final = piloto_fav if piloto_fav else ""
                    
                    # Orden exacto de tu DB: Fecha, Nombre, Pass, Whatsapp, Correo, Cumple, Piloto_Fav, Ruta_Foto, Escuderia
                    fila = [ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), fecha_cumple, piloto_final, "", esc]
                    tabla_jugadores.append_row(fila)
                    st.success(f"✅ ¡Bienvenido a la F1, {nu}! Ve a la pestaña de 'Acceso' para entrar a pits.")

    with tab3:
        st.title("Recuperar Telemetría")
        uo = st.text_input("Tu Alias de Piloto:", key="f_u")
        if st.button("🔍 Buscar en el Paddock"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j.empty:
                match = df_j[df_j['Nombre'].astype(str).str.strip() == uo.strip()]
                if not match.empty: 
                    st.success(f"🔑 Tu contraseña es: **{match.iloc[0]['Password']}**")
                else: 
                    st.error("❓ Ese piloto no aparece en nuestros registros.")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    es_admin = st.session_state['usuario_activo'] == "Sasian"
    
    with st.sidebar:
        st.markdown(f"### 🏎️ Pits: {st.session_state['usuario_activo']}")
        opciones = ["📝 Hacer Apuesta", "🏆 El Paddock"]
        if es_admin: 
            opciones.append("👑 Admin FIA")
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
        
        if gp_sel:
            bq, bc = False, False 
            
            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            ya_aposto, ap_p = False, {}
            if not df_q.empty:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
                if not filtro.empty:
                    ya_aposto, ap_p = True, filtro.iloc[-1].to_dict()
                    st.info("💡 Detecté una prueba guardada, pero los candados están apagados por hoy. Puedes capturar libremente.")

            # Esta función asegura que si es carrera nueva, regrese None (en blanco)
            def get_idx(campo):
                if ya_aposto and ap_p.get(campo) in pilotos:
                    return pilotos.index(ap_p.get(campo))
                return None

            st.markdown("### ⏱️ Calificación")
            q1_col, q2_col, q3_col = st.columns(3)
            # Agregamos key dinámica basada en la carrera para que se limpien al cambiar de GP
            with q1_col: q1 = st.selectbox("PP1 (Pole):", pilotos, index=get_idx('Qualy_P1'), key=f"q1_{gp_sel}", placeholder="Elige...", disabled=bq)
            with q2_col: q2 = st.selectbox("Qualy P2:", pilotos, index=get_idx('Qualy_P2'), key=f"q2_{gp_sel}", placeholder="Elige...", disabled=bq)
            with q3_col: q3 = st.selectbox("Qualy P3:", pilotos, index=get_idx('Qualy_P3'), key=f"q3_{gp_sel}", placeholder="Elige...", disabled=bq)
            
            st.write("---")
            st.markdown("### 🏁 Carrera")
            c4, c5, c6 = st.columns(3)
            with c4: g1 = st.selectbox("Ganador (P1):", pilotos, index=get_idx('Carrera_P1'), key=f"g1_{gp_sel}", placeholder="Elige...", disabled=bc)
            with c5: g2 = st.selectbox("Segundo (P2):", pilotos, index=get_idx('Carrera_P2'), key=f"g2_{gp_sel}", placeholder="Elige...", disabled=bc)
            with c6: g3 = st.selectbox("Tercer (P3):", pilotos, index=get_idx('Carrera_P3'), key=f"g3_{gp_sel}", placeholder="Elige...", disabled=bc)

            st.write("---")
            st.markdown("### 🎲 Bonos Especiales")
            b1, b2 = st.columns(2)
            with b1: vr = st.selectbox("🚀 Vuelta Rápida:", pilotos, index=get_idx('Vuelta_Rapida'), key=f"vr_{gp_sel}", placeholder="Elige...", disabled=bc)
            
            idx_ab = pilotos.index(ap_p.get('Primer_Abandono')) if ya_aposto and ap_p.get('Primer_Abandono') in pilotos else None
            with b2: ab = st.selectbox("💥 Primer Abandono (Opcional):", pilotos, index=idx_ab, key=f"ab_{gp_sel}", placeholder="Ninguno", disabled=bc)
            
            if st.button("🏎️ Sellar Apuesta / Actualizar"):
                # Validamos que no dejen espacios obligatorios en blanco
                if None in [q1, q2, q3, g1, g2, g3, vr]:
                    st.warning("⚠️ ¡Pits incompletos! Faltan pronósticos por llenar. El Bono Salado es el único opcional.")
                # Validamos la Bandera Negra (repetidos)
                elif len(set([q1, q2, q3])) < 3:
                    st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en la Calificación. Cámbialos.")
                elif len(set([g1, g2, g3])) < 3:
                    st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el podio de la Carrera. Cámbialos.")
                else:
                    v_ab = "🔒 CERRADO" if bc else (ab if ab else "")
                    fila = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, g1, g2, g3, vr, v_ab, 0]
                    tabla_quinielas.append_row(fila)
                    st.success("✅ ¡Apuesta sellada con éxito!")
                    st.rerun()

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
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \\n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos.")
        st.markdown("### 🎯 ARTÍCULO 2: El Podio (Precisión Absoluta)")
        st.success("Aquí no hay premios de consolación por 'casi' atinarle. O le das a la posición exacta o tienes cero.\\n* 🥇 **Ganador (P1):** +3 Puntos.\\n* 🥈 **Segundo (P2):** +3 Puntos.\\n* 🥉 **Tercer (P3):** +3 Puntos.\\n* ⏱️ **Pole Position (Qualy P1):** +3 Puntos.\\n* 🚀 **Vuelta Rápida:** +2 Puntos si adivinas quién hace el giro más rápido el domingo.")
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("Esta apuesta es **OPCIONAL**.\\n* ✅ **Si Acertaste:** Si tu piloto es el primero en abandonar, eres un genio del mal y te llevas **+5 Puntos** directos.\\n* ❌ **Si Fallaste:** Si sobrevive o alguien más abandona antes, te castigamos con **-2 Puntos**.\\n* 🛡️ **Tip:** Dejar el espacio en blanco es totalmente válido y te salva de perder puntos.")
        st.markdown("### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
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
            except: 
                st.error("❌ Error de comunicación.")

        with st.form("fia_form"):
            sel_car = st.selectbox("Gran Premio a Dictaminar:", carreras)
            idx1 = pilotos.index(st.session_state['auto_c1']) if st.session_state['auto_c1'] in pilotos else None
            idx2 = pilotos.index(st.session_state['auto_c2']) if st.session_state['auto_c2'] in pilotos else None
            idx3 = pilotos.index(st.session_state['auto_c3']) if st.session_state['auto_c3'] in pilotos else None

            st.markdown("### ⏱️ Resultados Calificación")
            cq1, cq2, cq3 = st.columns(3)
            with cq1: rq1 = st.selectbox("Pole Real (Q1):", pilotos)
            with cq2: rq2 = st.selectbox("Q2 Real:", pilotos)
            with cq3: rq3 = st.selectbox("Q3 Real:", pilotos)
            
            st.markdown("### 🏁 Resultados Carrera")
            c1, c2, c3 = st.columns(3)
            with c1: rg1 = st.selectbox("P1 Real:", pilotos, index=idx1)
            with c2: rg2 = st.selectbox("P2 Real:", pilotos, index=idx2)
            with c3: rg3 = st.selectbox("P3 Real:", pilotos, index=idx3)
            
            st.markdown("### 🎲 Bonos")
            b1, b2 = st.columns(2)
            with b1: rvr = st.selectbox("VR Real:", pilotos)
            with b2: rab = st.selectbox("Salado Real:", pilotos)

            if st.form_submit_button("⚖️ Repartir Puntos"):
                tabla_resultados.append_row([sel_car, rq1, rq2, rq3, rg1, rg2, rg3, rvr, rab])
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
