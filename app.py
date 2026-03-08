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

# LEER CALENDARIO DINÁMICO DESDE GOOGLE SHEETS
df_cal_global = pd.DataFrame(tabla_calendario.get_all_records())
lista_carreras_oficial = df_cal_global['Carrera'].tolist() if not df_cal_global.empty else []

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
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'auto_c1' not in st.session_state: st.session_state['auto_c1'] = None
if 'auto_c2' not in st.session_state: st.session_state['auto_c2'] = None
if 'auto_c3' not in st.session_state: st.session_state['auto_c3'] = None

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
                fecha_cump = cumple.strftime("%Y-%m-%d") if cumple else ""
                pil_f = piloto_fav if piloto_fav else ""
                tabla_jugadores.append_row([ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), fecha_cump, pil_f, "", esc])
                st.success(f"✅ ¡Bienvenido a la F1, {nu}! Ve a la pestaña de 'Acceso'.")

    with tab3:
        st.title("Recuperar Telemetría")
        uo = st.text_input("Tu Alias de Piloto:", key="f_u")
        if st.button("🔍 Buscar en el Paddock"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
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
        if es_admin: opciones.append("👑 Admin FIA")
        opciones.append("📖 Reglamento Oficial")
        menu = st.radio("Navegación", opciones)
        st.write("---")
        if st.button("🚪 Salir de Pits"):
            st.session_state['usuario_activo'] = None
            st.rerun()

    # EL NUEVO BANNER (Elegante, tamaño correcto y con banderas)
    st.markdown("""
        <div style="text-align: center; background: #15151e; padding: 15px; border-radius: 8px; border-bottom: 3px solid #E10600; margin-bottom: 20px;">
            <span style="font-family: 'Arial', sans-serif; font-size: 2.2rem; color: white; font-weight: 900; letter-spacing: 1px;">🏁 LIGA SASIANGP 2026 🏁</span>
        </div>
    """, unsafe_allow_html=True)

    if menu == "📝 Hacer Apuesta":
        st.subheader("Tu Pronóstico Oficial")
        gp_sel = st.selectbox("🌎 Selecciona Gran Premio:", lista_carreras_oficial, index=None, placeholder="Elige un Gran Premio...")
        
        if gp_sel:
            bq, bc = True, True 
            f = df_cal_global[df_cal_global['Carrera'] == gp_sel]
            if not f.empty:
                ahora = datetime.utcnow() - timedelta(hours=6)
                dt_q = pd.to_datetime(f.iloc[0]['Fecha_Qualy'], format="%H:%M %d-%m-%Y", errors='coerce')
                dt_c = pd.to_datetime(f.iloc[0]['Fecha_Carrera'], format="%H:%M %d-%m-%Y", errors='coerce')
                if pd.notna(dt_q) and ahora < (dt_q - timedelta(hours=1)): bq = False
                if pd.notna(dt_c) and ahora < (dt_c - timedelta(hours=1)): bc = False
            
            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            ya_aposto, ap_p = False, {}
            if not df_q.empty:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
                if not filtro.empty:
                    ya_aposto, ap_p = True, filtro.iloc[-1].to_dict()
                    st.info("💡 Parque Cerrado activo. Ya sellaste tu pronóstico para esta carrera.")

            def get_idx(campo): return pilotos.index(ap_p.get(campo)) if ya_aposto and ap_p.get(campo) in pilotos else None

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
            with b3: ab = st.selectbox("💥 Abandono (Opcional):", pilotos, index=idx_ab, key=f"ab_{gp_sel}", placeholder="Ninguno", disabled=bc or ya_aposto)
            
            if st.button("🏎️ Sellar Apuesta", disabled=ya_aposto):
                if None in [q1, q2, q3, g1, g2, g3, vr, pdia]:
                    st.warning("⚠️ ¡Pits incompletos! Faltan pronósticos por llenar.")
                elif len(set([q1, q2, q3])) < 3 or len(set([g1, g2, g3])) < 3:
                    st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el podio.")
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
            opcion_ver = st.selectbox("Selecciona la vista a analizar:", ["🏆 Total del Campeonato"] + lista_carreras_oficial)
            
            if opcion_ver == "🏆 Total del Campeonato":
                df_q['Puntos_Totales'] = pd.to_numeric(df_q['Puntos_Totales'], errors='coerce').fillna(0)
                res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False).reset_index(drop=True)
                st.dataframe(res, use_container_width=True)
            else:
                df_f = df_q[df_q['Carrera'] == opcion_ver].copy()
                if not df_f.empty:
                    def acortar_nombre(n): return str(n).split()[-1] if (pd.notna(n) and " " in str(n)) else str(n)
                    
                    todos_res = tabla_resultados.get_all_values()
                    r_of = {}
                    for fila in reversed(todos_res):
                        if len(fila) >= 10 and fila[0] == opcion_ver:
                            r_of = {'Q1': acortar_nombre(fila[1]), 'Q2': acortar_nombre(fila[2]), 'Q3': acortar_nombre(fila[3]), 
                                    'P1': acortar_nombre(fila[4]), 'P2': acortar_nombre(fila[5]), 'P3': acortar_nombre(fila[6]), 
                                    'VR': acortar_nombre(fila[7]), 'PD': acortar_nombre(fila[8]), 'Salado': acortar_nombre(fila[9])}
                            break

                    cols_apuestas = ["Qualy_P1", "Qualy_P2", "Qualy_P3", "Carrera_P1", "Carrera_P2", "Carrera_P3", "Vuelta_Rapida", "Piloto_Del_Dia", "Primer_Abandono"]
                    for c in cols_apuestas: 
                        if c in df_f.columns: df_f[c] = df_f[c].apply(acortar_nombre)

                    nombres_base = {"Qualy_P1": "Q1", "Qualy_P2": "Q2", "Qualy_P3": "Q3", "Carrera_P1": "P1", "Carrera_P2": "P2", "Carrera_P3": "P3", "Vuelta_Rapida": "VR", "Piloto_Del_Dia": "PD", "Primer_Abandono": "Salado", "Puntos_Totales": "Pts"}
                    
                    rename_dict = {}
                    for col_orig, col_corta in nombres_base.items():
                        if col_orig in df_f.columns:
                            if col_corta in r_of and r_of[col_corta] != "": rename_dict[col_orig] = f"{col_corta}\n({r_of[col_corta]})"
                            else: rename_dict[col_orig] = col_corta
                    
                    df_f = df_f.rename(columns=rename_dict)
                    cols_mostrar = ['Jugador'] + list(rename_dict.values())
                    df_mostrar = df_f[[c for c in cols_mostrar if c in df_f.columns]].copy()

                    def aplicar_colores(row):
                        styles = [''] * len(row)
                        for i, col_name in enumerate(row.index):
                            if col_name in ['Jugador', 'Pts'] or not r_of: continue
                            val = str(row[col_name]).strip()
                            if val in ["", "nan", "None", "🔒 CERRADO"]: continue
                            
                            base_col = col_name.split('\n')[0]
                            if base_col in r_of:
                                real_val = r_of[base_col]
                                if val == real_val: 
                                    styles[i] = 'color: #00e676; font-weight: bold;' # Verde exacto
                                elif base_col in ['P1','P2','P3'] and val in [r_of.get('P1'), r_of.get('P2'), r_of.get('P3')]: 
                                    styles[i] = 'color: #ffb300; font-weight: bold;' # Naranja consuelo
                                elif base_col in ['Q1','Q2','Q3'] and val in [r_of.get('Q1'), r_of.get('Q2'), r_of.get('Q3')]: 
                                    styles[i] = 'color: #ffb300; font-weight: bold;' # Naranja consuelo
                                else: 
                                    styles[i] = 'color: #ff5252; font-weight: bold;' # Rojo fallo
                        return styles

                    styled_df = df_mostrar.style.apply(aplicar_colores, axis=1)
                    styled_df = styled_df.set_properties(**{'text-align': 'center'}, subset=df_mostrar.columns[1:])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos.")
        
        st.markdown("### 🎯 ARTÍCULO 2: Sistema de Puntuación Detallado")
        st.success("""
        Para las secciones de **Calificación (Q1, Q2, Q3)** y **Carrera (P1, P2, P3)**, el puntaje se calcula así:
        * 🥇 **Posición Exacta:** **+3 Puntos** si aciertas al piloto en el lugar exacto que pronosticaste.
        * 🥈 **Acierto Desordenado:** **+1 Punto** si tu piloto queda en el podio (Top 3 de Q o P) pero en una posición distinta a la que elegiste.
        
        **Bonos Adicionales:**
        * 🚀 **Vuelta Rápida:** **+2 Puntos** por acierto exacto.
        * 🌟 **Piloto del Día:** **+2 Puntos** por acierto exacto.
        """)
        
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("""
        Esta apuesta es **OPCIONAL** (Puedes dejarla en 'Ninguno').
        * ✅ **Si Acertaste:** Si tu piloto es el primero en abandonar, eres un genio del mal y te llevas **+5 Puntos** directos.
        * ❌ **Si Fallaste:** Si sobrevive o alguien más abandona antes, la FIA te castiga con **-5 Puntos**.
        """)
        
        st.markdown("### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
        st.error("Los resultados son inyectados directamente por la telemetría oficial de la API y validados por el mismísimo **Sasian**. La decisión final es absoluta e inapelable.")

    elif menu == "👑 Admin FIA":
        st.subheader("Control del Director de Carrera")
        sel_car = st.selectbox("Gran Premio a Dictaminar:", lista_carreras_oficial)
        
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

        todos_resultados = tabla_resultados.get_all_values()
        res_previos = {}
        for fila in reversed(todos_resultados):
            if len(fila) >= 10 and fila[0] == sel_car:
                res_previos = {
                    'rq1': fila[1], 'rq2': fila[2], 'rq3': fila[3],
                    'rg1': fila[4], 'rg2': fila[5], 'rg3': fila[6],
                    'rvr': fila[7], 'rpd': fila[8], 'rab': fila[9]
                }
                break

        if res_previos: st.info("💡 Ya hay resultados oficiales guardados para esta carrera.")

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
                tabla_resultados.append_row([sel_car, rq1, rq2, rq3, rg1, rg2, rg3, rvr, rpd, rab if rab else ""])
                
                celdas_actualizar = []
                t_q = tabla_quinielas.get_all_values()
                
                podio_c = [rg1, rg2, rg3]
                podio_q = [rq1, rq2, rq3]
                
                for idx, fila in enumerate(t_q[1:], start=2):
                    fila += [""] * (13 - len(fila))
                    if fila[2] == sel_car:
                        p = 0
                        # Matemáticas de Carrera
                        ap_c = [fila[6].strip(), fila[7].strip(), fila[8].strip()]
                        for i, ap in enumerate(ap_c):
                            if ap == podio_c[i] and ap != "": p += 3
                            elif ap in podio_c and ap != "": p += 1
                        
                        # Matemáticas de Qualy
                        ap_q = [fila[3].strip(), fila[4].strip(), fila[5].strip()]
                        for i, ap in enumerate(ap_q):
                            if ap == podio_q[i] and ap != "": p += 3
                            elif ap in podio_q and ap != "": p += 1
                        
                        # Matemáticas de Bonos
                        ap_vr, ap_pd, ap_ab = fila[9].strip(), fila[10].strip(), fila[11].strip()
                        
                        if ap_vr == rvr and rvr != "": p += 2
                        if ap_pd == rpd and rpd != "": p += 2
                        
                        # Matemáticas Salado
                        if ap_ab != "" and ap_ab != "🔒 CERRADO":
                            if ap_ab == rab and rab != "": p += 5
                            else: p -= 5
                            
                        celdas_actualizar.append(gspread.Cell(row=idx, col=13, value=p))
                
                if celdas_actualizar:
                    tabla_quinielas.update_cells(celdas_actualizar)
                st.success("🏆 ¡Puntos calculados con precisión absoluta y guardados!")
