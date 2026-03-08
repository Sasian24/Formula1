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
                    st.error("❌ Acceso Denegado.")

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
                st.warning("⚠️ Datos obligatorios faltantes.")
            elif nu.strip() in existentes: 
                st.error("❌ Alias ocupado.")
            else:
                ahora_mx = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
                f_c = cumple.strftime("%Y-%m-%d") if cumple else ""
                tabla_jugadores.append_row([ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), f_c, piloto_fav if piloto_fav else "", "", esc])
                st.success(f"✅ ¡Bienvenido {nu}!")

    with tab3:
        st.title("Recuperar Clave")
        uo = st.text_input("Tu Alias:", key="f_u")
        if st.button("🔍 Buscar"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            match = df_j[df_j['Nombre'].astype(str).str.strip() == uo.strip()]
            if not match.empty: 
                st.success(f"🔑 Tu clave es: **{match.iloc[0]['Password']}**")
            else: 
                st.error("❓ Piloto no registrado.")

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

    st.markdown("""<div style="text-align: center; background: #1e1e1e; padding: 10px; border-radius: 12px; border-bottom: 4px solid #E10600;"><span style="font-family: Impact; font-size: 3rem; color: #E10600; font-style: italic;">F1 SasianGP</span></div>""", unsafe_allow_html=True)

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
                    st.info("💡 Parque Cerrado activo. Ya sellaste tu pronóstico.")

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
            with b3: ab = st.selectbox("💥 Abandono (Opcional):", pilotos, index=idx_ab, key=f"ab_{gp_sel}", placeholder="Ninguno", disabled=bc or ya_aposto)
            
            if st.button("🏎️ Sellar Apuesta", disabled=ya_aposto):
                if None in [q1, q2, q3, g1, g2, g3, vr, pdia]:
                    st.warning("⚠️ Pronósticos incompletos.")
                elif len(set([q1, q2, q3])) < 3 or len(set([g1, g2, g3])) < 3:
                    st.error("❌ Pilotos repetidos.")
                else:
                    v_ab = ab if ab else ""
                    fila = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, g1, g2, g3, vr, pdia, v_ab, 0]
                    tabla_quinielas.append_row(fila)
                    st.success("✅ ¡Apuesta sellada!")
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
        if not df_q.empty:
            opcion_ver = st.selectbox("Selecciona vista:", ["🏆 Total"] + lista_carreras_oficial)
            if opcion_ver == "🏆 Total":
                df_q['Puntos_Totales'] = pd.to_numeric(df_q['Puntos_Totales'], errors='coerce').fillna(0)
                res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False).reset_index(drop=True)
                st.dataframe(res, use_container_width=True)
            else:
                df_f = df_q[df_q['Carrera'] == opcion_ver].copy()
                if not df_f.empty:
                    def ac_n(n): return n.split()[-1] if (pd.notna(n) and " " in str(n)) else n
                    
                    todos_res = tabla_resultados.get_all_values()
                    r_of = {}
                    for fila in reversed(todos_res):
                        if len(fila) >= 10 and fila[0] == opcion_ver:
                            r_of = {'Q1': ac_n(fila[1]), 'Q2': ac_n(fila[2]), 'Q3': ac_n(fila[3]), 'P1': ac_n(fila[4]), 'P2': ac_n(fila[5]), 'P3': ac_n(fila[6]), 'VR': ac_n(fila[7]), 'PD': ac_n(fila[8]), 'Salado': ac_n(fila[9])}
                            break

                    columnas = ["Qualy_P1", "Qualy_P2", "Qualy_P3", "Carrera_P1", "Carrera_P2", "Carrera_P3", "Vuelta_Rapida", "Piloto_Del_Dia", "Primer_Abandono"]
                    for col in columnas:
                        if col in df_f.columns: df_f[col] = df_f[col].apply(ac_n)

                    rename_map = {"Qualy_P1": "Q1", "Qualy_P2": "Q2", "Qualy_P3": "Q3", "Carrera_P1": "P1", "Carrera_P2": "P2", "Carrera_P3": "P3", "Vuelta_Rapida": "VR", "Piloto_Del_Dia": "PD", "Primer_Abandono": "Salado", "Puntos_Totales": "Pts"}
                    df_f = df_f.rename(columns=rename_map)
                    
                    def style_txt(row):
                        styles = [''] * len(row)
                        for i, col in enumerate(row.index):
                            if col in ['Jugador', 'Pts']: continue
                            val = str(row[col]).strip()
                            if val == "" or val == "nan" or not r_of: continue
                            base = col
                            if base in r_of:
                                real = r_of[base]
                                if val == real: styles[i] = 'color: #00e676; font-weight: bold;'
                                elif base in ['P1','P2','P3']:
                                    if val in [r_of.get('P1'),r_of.get('P2'),r_of.get('P3')]: styles[i] = 'color: #ffb300; font-weight: bold;'
                                    else: styles[i] = 'color: #ff5252; font-weight: bold;'
                                elif base in ['Q1','Q2','Q3']:
                                    if val in [r_of.get('Q1'),r_of.get('Q2'),r_of.get('Q3')]: styles[i] = 'color: #ffb300; font-weight: bold;'
                                    else: styles[i] = 'color: #ff5252; font-weight: bold;'
                                else: styles[i] = 'color: #ff5252; font-weight: bold;'
                        return styles

                    st.dataframe(df_f[['Jugador','Q1','Q2','Q3','P1','P2','P3','VR','PD','Salado','Pts']].style.apply(style_txt, axis=1), use_container_width=True, hide_index=True)

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.success("""
        **ARTÍCULO 2: SISTEMA DE PUNTUACIÓN**
        * 🥇 **Posición Exacta:** **+3 Puntos** (Q1, Q2, Q3 y P1, P2, P3).
        * 🥈 **Acierto Desordenado:** **+1 Punto** si el piloto queda en el podio (Top 3) pero en otro lugar.
        * 🚀 **Vuelta Rápida:** **+2 Puntos**.
        * 🌟 **Piloto del Día:** **+2 Puntos**.
        * ☠️ **Bono Salado:** **+5 Puntos** acierto / **-5 Puntos** error. (Opcional)
        """)

    elif menu == "👑 Admin FIA":
        st.subheader("Dictaminar Gran Premio")
        sel_car = st.selectbox("Carrera:", lista_carreras_oficial)
        if st.button("⚡ API Telemetría"):
            try:
                r = requests.get("https://api.jolpi.ca/ergast/f1/current/last/results.json").json()
                res_api = r['MRData']['RaceTable']['Races'][0]['Results']
                st.session_state['auto_c1'] = traductor_api.get(res_api[0]['Driver']['familyName'], None)
                st.session_state['auto_c2'] = traductor_api.get(res_api[1]['Driver']['familyName'], None)
                st.session_state['auto_c3'] = traductor_api.get(res_api[2]['Driver']['familyName'], None)
                st.success("✅ Datos API cargados.")
            except: st.error("❌ Error API.")

        with st.form("fia_f"):
            c1, c2, c3 = st.columns(3)
            with c1: rq1 = st.selectbox("Q1:", pilotos); rg1 = st.selectbox("P1:", pilotos, index=pilotos.index(st.session_state.get('auto_c1')) if st.session_state.get('auto_c1') in pilotos else None)
            with c2: rq2 = st.selectbox("Q2:", pilotos); rg2 = st.selectbox("P2:", pilotos, index=pilotos.index(st.session_state.get('auto_c2')) if st.session_state.get('auto_c2') in pilotos else None)
            with c3: rq3 = st.selectbox("Q3:", pilotos); rg3 = st.selectbox("P3:", pilotos, index=pilotos.index(st.session_state.get('auto_c3')) if st.session_state.get('auto_c3') in pilotos else None)
            b1, b2, b3 = st.columns(3)
            with b1: rvr = st.selectbox("VR:", pilotos)
            with b2: rpd = st.selectbox("PD:", pilotos)
            with b3: rab = st.selectbox("Abandono:", pilotos, index=None)

            if st.form_submit_button("⚖️ Repartir Puntos"):
                tabla_resultados.append_row([sel_car, rq1, rq2, rq3, rg1, rg2, rg3, rvr, rpd, rab if rab else ""])
                celdas_act = []
                t_q = tabla_quinielas.get_all_values()
                for idx, fila in enumerate(t_q[1:], start=2):
                    fila += [""] * (13 - len(fila))
                    if fila[2] == sel_car:
                        p = 0
                        pod_c = [rg1, rg2, rg3]
                        for i, ap in enumerate([fila[6], fila[7], fila[8]]):
                            if ap == pod_c[i]: p += 3
                            elif ap in pod_c and ap != "": p += 1
                        pod_q = [rq1, rq2, rq3]
                        for i, ap in enumerate([fila[3], fila[4], fila[5]]):
                            if ap == pod_q[i]: p += 3
                            elif ap in pod_q and ap != "": p += 1
                        if fila[9] == rvr and rvr != "": p += 2
                        if fila[10] == rpd and rpd != "": p += 2
                        if fila[11] != "":
                            if fila[11] == rab: p += 5
                            else: p -= 5
                        celdas_act.append(gspread.Cell(row=idx, col=13, value=p))
                if celdas_act: tabla_quinielas.update_cells(celdas_act)
                st.success("🏆 Puntos repartidos correctamente.")
