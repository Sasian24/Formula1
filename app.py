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

# --- 5. INTERFAZ DE ACCESO ---
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
            
            if not nu or not np or not esc: 
                st.warning("⚠️ Debes llenar al menos el Alias, Contraseña y Escudería.")
            elif nu.strip() in existentes: 
                st.error("❌ Ese Alias ya está ocupado en el Paddock.")
            else:
                ahora_mx = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
                fecha_cumple = cumple.strftime("%Y-%m-%d") if cumple else ""
                piloto_final = piloto_fav if piloto_fav else ""
                
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
        opciones = ["📝 Hacer Apuesta", "🏆 El Paddock", "📊 Paddock Detallado"]
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
            bq, bc = True, True 
            f = df_cal[df_cal['Carrera'] == gp_sel]
            if not f.empty:
                ahora = datetime.utcnow() - timedelta(hours=6)
                dt_q = pd.to_datetime(f.iloc[0]['Fecha_Qualy'], format="%H:%M %d-%m-%Y", errors='coerce')
                dt_c = pd.to_datetime(f.iloc[0]['Fecha_Carrera'], format="%H:%M %d-%m-%Y", errors='coerce')
                if pd.notna(dt_q) and ahora < (dt_q + timedelta(hours=1)): bq = False
                if pd.notna(dt_c) and ahora < (dt_c + timedelta(hours=1)): bc = False
            
            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            ya_aposto, ap_p = False, {}
            if not df_q.empty:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
                if not filtro.empty:
                    ya_aposto, ap_p = True, filtro.iloc[-1].to_dict()
                    st.info("💡 Parque Cerrado activo. Ya sellaste tu pronóstico para esta carrera.")

            def get_idx(campo):
                if ya_aposto and ap_p.get(campo) in pilotos:
                    return pilotos.index(ap_p.get(campo))
                return None

            st.markdown("### ⏱️ Calificación")
            q1_col, q2_col, q3_col = st.columns(3)
            with q1_col: q1 = st.selectbox("PP1 (Pole):", pilotos, index=get_idx('Qualy_P1'), key=f"q1_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            with q2_col: q2 = st.selectbox("Qualy P2:", pilotos, index=get_idx('Qualy_P2'), key=f"q2_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            with q3_col: q3 = st.selectbox("Qualy P3:", pilotos, index=get_idx('Qualy_P3'), key=f"q3_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            
            st.write("---")
            st.markdown("### 🏁 Carrera")
            c4, c5, c6 = st.columns(3)
            with c4: g1 = st.selectbox("Ganador (P1):", pilotos, index=get_idx('Carrera_P1'), key=f"g1_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with c5: g2 = st.selectbox("Segundo (P2):", pilotos, index=get_idx('Carrera_P2'), key=f"g2_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with c6: g3 = st.selectbox("Tercer (P3):", pilotos, index=get_idx('Carrera_P3'), key=f"g3_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)

            st.write("---")
            st.markdown("### 🎲 Bonos Especiales")
            b1, b2, b3 = st.columns(3)
            with b1: vr = st.selectbox("🚀 Vuelta Rápida:", pilotos, index=get_idx('Vuelta_Rapida'), key=f"vr_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with b2: pdia = st.selectbox("🌟 Piloto del Día:", pilotos, index=get_idx('Piloto_Del_Dia'), key=f"pd_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            
            idx_ab = pilotos.index(ap_p.get('Primer_Abandono')) if ya_aposto and ap_p.get('Primer_Abandono') in pilotos else None
            with b3: ab = st.selectbox("💥 Primer Abandono (Opcional):", pilotos, index=idx_ab, key=f"ab_{gp_sel}", placeholder="Ninguno", disabled=bc or ya_aposto)
            
            if st.button("🏎️ Sellar Apuesta", disabled=ya_aposto):
                if None in [q1, q2, q3, g1, g2, g3, vr, pdia]:
                    st.warning("⚠️ ¡Pits incompletos! Faltan pronósticos por llenar. El Bono Salado es el único opcional.")
                elif len(set([q1, q2, q3])) < 3:
                    st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en la Calificación. Cámbialos.")
                elif len(set([g1, g2, g3])) < 3:
                    st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el podio de la Carrera. Cámbialos.")
                else:
                    v_ab = "🔒 CERRADO" if bc else (ab if ab else "")
                    fila = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, g1, g2, g3, vr, pdia, v_ab, 0]
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

    elif menu == "📊 Paddock Detallado":
        st.subheader("🔍 Análisis de Telemetría (Paddock Detallado)")
        df_q = pd.DataFrame(tabla_quinielas.get_all_records())
        
        if df_q.empty:
            st.info("Aún no hay telemetría registrada en el servidor.")
        else:
            opcion_ver = st.selectbox("Selecciona la vista a analizar:", ["🏆 Total del Campeonato"] + carreras)
            
            if opcion_ver == "🏆 Total del Campeonato":
                df_q['Puntos_Totales'] = pd.to_numeric(df_q['Puntos_Totales'], errors='coerce').fillna(0)
                res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False).reset_index(drop=True)
                st.dataframe(res, use_container_width=True)
            else:
                df_filtro = df_q[df_q['Carrera'] == opcion_ver].copy()
                if df_filtro.empty:
                    st.warning(f"Ningún piloto ha metido su monoplaza a pits para el {opcion_ver} todavía.")
                else:
                    def acortar_nombre(nombre):
                        if pd.isna(nombre) or nombre == "" or nombre == "🔒 CERRADO": return nombre
                        partes = nombre.split()
                        return partes[-1] if len(partes) > 1 else nombre

                    todos_resultados = tabla_resultados.get_all_values()
                    res_oficiales = {}
                    for fila in reversed(todos_resultados):
                        if len(fila) >= 10 and fila[0] == opcion_ver:
                            res_oficiales = {
                                'Q1': acortar_nombre(fila[1]), 'Q2': acortar_nombre(fila[2]), 'Q3': acortar_nombre(fila[3]),
                                'P1': acortar_nombre(fila[4]), 'P2': acortar_nombre(fila[5]), 'P3': acortar_nombre(fila[6]),
                                'VR': acortar_nombre(fila[7]), 'PD': acortar_nombre(fila[8]), 'Salado': acortar_nombre(fila[9])
                            }
                            break

                    columnas_apuestas = ["Qualy_P1", "Qualy_P2", "Qualy_P3", "Carrera_P1", "Carrera_P2", "Carrera_P3", "Vuelta_Rapida", "Piloto_Del_Dia", "Primer_Abandono"]
                    for col in columnas_apuestas:
                        if col in df_filtro.columns:
                            df_filtro[col] = df_filtro[col].apply(acortar_nombre)

                    nombres_base = {
                        "Qualy_P1": "Q1", "Qualy_P2": "Q2", "Qualy_P3": "Q3",
                        "Carrera_P1": "P1", "Carrera_P2": "P2", "Carrera_P3": "P3",
                        "Vuelta_Rapida": "VR", "Piloto_Del_Dia": "PD", "Primer_Abandono": "Salado", 
                        "Puntos_Totales": "Pts"
                    }
                    
                    rename_dict = {}
                    for col_orig, col_corta in nombres_base.items():
                        if col_orig in df_filtro.columns:
                            if col_corta in res_oficiales and res_oficiales[col_corta] != "":
                                rename_dict[col_orig] = f"{col_corta}\n({res_oficiales[col_corta]})"
                            else:
                                rename_dict[col_orig] = col_corta
                    
                    df_filtro = df_filtro.rename(columns=rename_dict)
                    cols_mostrar = ['Jugador'] + list(rename_dict.values())
                    df_mostrar = df_filtro[[c for c in cols_mostrar if c in df_filtro.columns]].copy()

                    def aplicar_colores(row):
                        styles = [''] * len(row)
                        for i, col_name in enumerate(row.index):
                            if col_name == 'Jugador' or col_name == 'Pts': continue
                            val = str(row[col_name]).strip()
                            if val == "" or val == "nan" or val == "🔒 CERRADO" or not res_oficiales: continue
                            base_col = col_name.split('\n')[0]
                            if base_col in res_oficiales:
                                real_val = res_oficiales[base_col]
                                if val == real_val:
                                    styles[i] = 'color: #00e676; font-weight: bold;'
                                elif base_col in ['P1', 'P2', 'P3']:
                                    if val in [res_oficiales.get('P1'), res_oficiales.get('P2'), res_oficiales.get('P3')]:
                                        styles[i] = 'color: #ffb300; font-weight: bold;'
                                    else: styles[i] = 'color: #ff5252; font-weight: bold;'
                                elif base_col in ['Q1', 'Q2', 'Q3']:
                                    if val in [res_oficiales.get('Q1'), res_oficiales.get('Q2'), res_oficiales.get('Q3')]:
                                        styles[i] = 'color: #ffb300; font-weight: bold;'
                                    else: styles[i] = 'color: #ff5252; font-weight: bold;'
                                else: styles[i] = 'color: #ff5252; font-weight: bold;'
                        return styles

                    styled_df = df_mostrar.style.apply(aplicar_colores, axis=1)
                    styled_df = styled_df.set_properties(**{'text-align': 'center'}, subset=df_mostrar.columns[1:])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \\n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos.")
        
        st.markdown("### 🎯 ARTÍCULO 2: Sistema de Puntuación Detallado")
        st.success("""
        Para las secciones de **Calificación (Q1, Q2, Q3)** y **Carrera (P1, P2, P3)**, el puntaje se calcula así:
        * 🥇 **Posición Exacta:** **+3 Puntos** si aciertas al piloto en el lugar exacto que pronosticaste.
        * 🥈 **Acierto Desordenado:** **+1 Punto** si tu piloto queda en el podio (Top 3) pero en una posición distinta a la que elegiste.
        
        **Ejemplo:** Si pones a Norris en P1 y queda en P2, obtienes **+1 punto**. Si queda en P1, obtienes **+3 puntos**.
        
        **Bonos Adicionales:**
        * 🚀 **Vuelta Rápida:** **+2 Puntos** por acierto exacto.
        * 🌟 **Piloto del Día:** **+2 Puntos** por acierto exacto.
        """)
        
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
            except: st.error("❌ Error de comunicación.")

        sel_car = st.selectbox("Gran Premio a Dictaminar:", carreras)
        todos_resultados = tabla_resultados.get_all_values()
        res_previos = {}
        for fila in reversed(todos_resultados):
            if len(fila) >= 10 and fila[0] == sel_car:
                res_previos = {'rq1': fila[1], 'rq2': fila[2], 'rq3': fila[3], 'rg1': fila[4], 'rg2': fila[5], 'rg3': fila[6], 'rvr': fila[7], 'rpd': fila[8], 'rab': fila[9]}
                break

        def get_idx_res(llave, d_v=None):
            if res_previos and res_previos.get(llave) in pilotos: return pilotos.index(res_previos[llave])
            if d_v in pilotos: return pilotos.index(d_v)
            return None

        with st.form("fia_form"):
            st.markdown("### ⏱️ Resultados Calificación")
            cq1, cq2, cq3 = st.columns(3)
            with cq1: rq1 = st.selectbox("Pole Real (Q1):", pilotos, index=get_idx_res('rq1'))
            with cq2: rq2 = st.selectbox("Q2 Real:", pilotos, index=get_idx_res('rq2'))
            with cq3: rq3 = st.selectbox("Q3 Real:", pilotos, index=get_idx_res('rq3'))
            st.markdown("### 🏁 Resultados Carrera")
            c1, c2, c3 = st.columns(3)
            with c1: rg1 = st.selectbox("P1 Real:", pilotos, index=get_idx_res('rg1', st.session_state.get('auto_c1')))
            with c2: rg2 = st.selectbox("P2 Real:", pilotos, index=get_idx_res('rg2', st.session_state.get('auto_c2')))
            with c3: rg3 = st.selectbox("P3 Real:", pilotos, index=get_idx_res('rg3', st.session_state.get('auto_c3')))
            st.markdown("### 🎲 Bonos")
            b1, b2, b3 = st.columns(3)
            with b1: rvr = st.selectbox("VR Real:", pilotos, index=get_idx_res('rvr'))
            with b2: rpd = st.selectbox("Piloto del Día Real:", pilotos, index=get_idx_res('rpd'))
            idx_rab = pilotos.index(res_previos['rab']) if res_previos and res_previos.get('rab') in pilotos else None
            with b3: rab = st.selectbox("Salado Real:", pilotos, index=idx_rab, placeholder="Ninguno")

            if st.form_submit_button("⚖️ Repartir Puntos"):
                tabla_resultados.append_row([sel_car, rq1, rq2, rq3, rg1, rg2, rg3, rvr, rpd, rab])
                celdas_act = []
                t_q = tabla_quinielas.get_all_values()
                for idx, fila in enumerate(t_q[1:], start=2):
                    fila += [""] * (13 - len(fila))
                    if fila[2] == sel_car:
                        p = 0
                        podio_c = [rg1, rg2, rg3]
                        for i, ap_p in enumerate([fila[6], fila[7], fila[8]], 0):
                            if ap_p == podio_c[i]: p += 3
                            elif ap_p in podio_c and ap_p != "": p += 1
                        podio_q = [rq1, rq2, rq3]
                        for i, ap_q in enumerate([fila[3], fila[4], fila[5]], 0):
                            if ap_q == podio_q[i]: p += 3
                            elif ap_q in podio_q and ap_q != "": p += 1
                        if fila[9] == rvr and fila[9] != "": p += 2
                        if fila[10] == rpd and fila[10] != "": p += 2
                        if fila[11] != "" and fila[11] != "🔒 CERRADO":
                            if fila[11] == rab: p += 5
                            else: p -= 2
                        celdas_act.append(gspread.Cell(row=idx, col=13, value=p))
                if celdas_act: tabla_quinielas.update_cells(celdas_act)
                st.success("🏆 ¡Puntos calculados con precisión suiza!")
