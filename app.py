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
if not df_cal_global.empty:
    df_cal_global.columns = [str(c).strip() for c in df_cal_global.columns]
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
        u = st.text_input("Alias de Piloto:", key="l_u")
        p = st.text_input("Contraseña:", type="password", key="l_p")
        if st.button("🏁 Arrancar Motores"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            if not df_j[(df_j['Nombre']==u.strip()) & (df_j['Password']==p.strip())].empty:
                st.session_state['usuario_activo'] = u.strip()
                st.rerun()
            else: st.error("❌ Acceso Denegado.")
    with tab2:
        nu = st.text_input("Alias *", key="r_u")
        np = st.text_input("Contraseña *", type="password", key="r_p")
        wp = st.text_input("WhatsApp", key="r_w")
        mail = st.text_input("Correo", key="r_m")
        cumple = st.date_input("Cumpleaños", value=None)
        pil_f = st.selectbox("Piloto Favorito", pilotos, index=None)
        esc = st.selectbox("Escudería *", list(url_logos.keys()))
        if st.button("✍️ Firmar Contrato"):
            ahora_mx = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
            tabla_jugadores.append_row([ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), cumple.strftime("%Y-%m-%d") if cumple else "", pil_f if pil_f else "", "", esc])
            st.success("✅ ¡Bienvenido!")
    with tab3:
        uo = st.text_input("Alias para recuperar:", key="f_u")
        if st.button("🔍 Buscar"):
            df_j = pd.DataFrame(tabla_jugadores.get_all_records())
            match = df_j[df_j['Nombre'] == uo.strip()]
            if not match.empty: st.success(f"🔑 Tu clave: {match.iloc[0]['Password']}")
            else: st.error("No encontrado.")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    es_admin = st.session_state['usuario_activo'] == "Sasian"
    with st.sidebar:
        st.markdown(f"### 🏎️ Pits: {st.session_state['usuario_activo']}")
        menu = st.radio("Navegación", ["📝 Hacer Apuesta", "🏆 El Paddock", "📊 Paddock Detallado", "👑 Admin FIA", "📖 Reglamento Oficial"])
        if st.button("🚪 Salir"):
            st.session_state['usuario_activo'] = None
            st.rerun()

    # --- BANNER ORIGINAL RESTAURADO (CONGELADO) ---
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #1e1e1e; padding: 10px 20px; border-radius: 12px; border-bottom: 4px solid #E10600; margin-bottom: 20px;">
            <span style="font-size: 2.5rem;">🏁</span>
            <div style="text-align: center;">
                <span style="font-family: Impact, sans-serif; font-size: 3.5rem; color: #E10600; font-style: italic; padding-right: 2px;">F1</span>
                <span style="font-family: Arial, sans-serif; font-size: 0.9rem; color: #E10600; font-weight: bold; vertical-align: super;">Sasian&reg;</span>
            </div>
            <span style="font-size: 2.5rem;">🏁</span>
        </div>
    """, unsafe_allow_html=True)

    if menu == "📝 Hacer Apuesta":
        gp_sel = st.selectbox("🌎 Selecciona GP:", lista_carreras_oficial, index=None, placeholder="Elige un Gran Premio...")
        if gp_sel:
            bq, bc, bs = True, True, True
            hora_q_txt, hora_c_txt, hora_s_txt = "", "", ""
            f = df_cal_global[df_cal_global['Carrera'] == gp_sel]
            es_sprint = False
            
            if not f.empty:
                if 'Es_Sprint' in f.columns:
                    es_sprint_val = str(f.iloc[0]['Es_Sprint']).strip().upper()
                else:
                    es_sprint_val = 'NO'
                    
                es_sprint = es_sprint_val in ['SI', 'SÍ', 'TRUE', '1', 'S']
                
                fecha_q_str = f.iloc[0].get('Fecha_Qualy', '')
                fecha_c_str = f.iloc[0].get('Fecha_Carrera', '')
                fecha_s_str = f.iloc[0].get('Fecha_Sprint', '') if 'Fecha_Sprint' in f.columns else ""
                
                if es_sprint: 
                    st.info(f"🕒 **Horarios Oficiales:** Qualy: {fecha_q_str} | Sprint: {fecha_s_str} | Carrera: {fecha_c_str} (🔥 Fin de Semana SPRINT)")
                else: 
                    st.info(f"🕒 **Horarios Oficiales:** Qualy: {fecha_q_str} | Carrera: {fecha_c_str}")

                ahora = datetime.utcnow() - timedelta(hours=6)
                dt_q = pd.to_datetime(fecha_q_str, format="%H:%M %d-%m-%Y", errors='coerce')
                dt_c = pd.to_datetime(fecha_c_str, format="%H:%M %d-%m-%Y", errors='coerce')
                dt_s = pd.to_datetime(fecha_s_str, format="%H:%M %d-%m-%Y", errors='coerce')
                
                if pd.notna(dt_q):
                    hora_q_txt = dt_q.strftime("%H:%M")
                    if ahora < (dt_q - timedelta(hours=1)): bq = False
                
                if pd.notna(dt_c):
                    hora_c_txt = dt_c.strftime("%H:%M")
                    if ahora < (dt_c - timedelta(hours=1)): bc = False
                
                if es_sprint:
                    if pd.notna(dt_s):
                        hora_s_txt = dt_s.strftime("%H:%M")
                        if ahora < (dt_s - timedelta(hours=1)): bs = False
                    else:
                        bs = bq
                    
            df_q = pd.DataFrame(tabla_quinielas.get_all_records())
            if not df_q.empty: df_q.columns = [str(c).strip() for c in df_q.columns]
            
            filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
            ya_aposto, ap_p = not filtro.empty, filtro.iloc[-1].to_dict() if not filtro.empty else {}
            if ya_aposto: st.warning("🔒 Parque Cerrado activo. Ya sellaste tu pronóstico para esta carrera.")

            def get_idx(campo): return pilotos.index(ap_p.get(campo)) if ya_aposto and ap_p.get(campo) in pilotos else None

            # --- QUALY ---
            q_title = f" ({hora_q_txt} hrs CDMX)" if hora_q_txt else ""
            st.markdown(f"### ⏱️ Calificación{q_title}")
            q1_col, q2_col, q3_col = st.columns(3)
            with q1_col: q1 = st.selectbox("Q1:", pilotos, index=get_idx('Qualy_P1'), key=f"q1_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            with q2_col: q2 = st.selectbox("Q2:", pilotos, index=get_idx('Qualy_P2'), key=f"q2_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            with q3_col: q3 = st.selectbox("Q3:", pilotos, index=get_idx('Qualy_P3'), key=f"q3_{gp_sel}", placeholder="Elige...", disabled=bq or ya_aposto)
            
            q_selections = [x for x in [q1, q2, q3] if x is not None]
            hay_error_q = len(q_selections) != len(set(q_selections))
            if hay_error_q: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en la Calificación. Cámbialos.")

            st.write("---")
            
            # --- SPRINT (DINÁMICO) ---
            s1, s2, s3 = None, None, None
            hay_error_s = False
            if es_sprint:
                s_title = f" ({hora_s_txt} hrs CDMX)" if hora_s_txt else ""
                st.markdown(f"### 🔥 Carrera Sprint{s_title}")
                s1_col, s2_col, s3_col = st.columns(3)
                with s1_col: s1 = st.selectbox("Sprint P1:", pilotos, index=get_idx('Sprint_P1'), key=f"s1_{gp_sel}", placeholder="Elige...", disabled=bs or ya_aposto)
                with s2_col: s2 = st.selectbox("Sprint P2:", pilotos, index=get_idx('Sprint_P2'), key=f"s2_{gp_sel}", placeholder="Elige...", disabled=bs or ya_aposto)
                with s3_col: s3 = st.selectbox("Sprint P3:", pilotos, index=get_idx('Sprint_P3'), key=f"s3_{gp_sel}", placeholder="Elige...", disabled=bs or ya_aposto)
                
                s_selections = [x for x in [s1, s2, s3] if x is not None]
                hay_error_s = len(s_selections) != len(set(s_selections))
                if hay_error_s: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el Sprint. Cámbialos.")
                st.write("---")
            
            # --- CARRERA ---
            c_title = f" ({hora_c_txt} hrs CDMX)" if hora_c_txt else ""
            st.markdown(f"### 🏁 Carrera Principal{c_title}")
            c1_col, c2_col, c3_col = st.columns(3)
            with c1_col: g1 = st.selectbox("P1:", pilotos, index=get_idx('Carrera_P1'), key=f"g1_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with c2_col: g2 = st.selectbox("P2:", pilotos, index=get_idx('Carrera_P2'), key=f"g2_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with c3_col: g3 = st.selectbox("P3:", pilotos, index=get_idx('Carrera_P3'), key=f"g3_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            
            c_selections = [x for x in [g1, g2, g3] if x is not None]
            hay_error_c = len(c_selections) != len(set(c_selections))
            if hay_error_c: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el podio de la Carrera. Cámbialos.")

            st.write("---")
            
            # --- BONOS ---
            st.markdown("### 🎲 Bonos Especiales")
            b1_col, b2_col, b3_col = st.columns(3)
            with b1_col: vr = st.selectbox("🚀 VR:", pilotos, index=get_idx('Vuelta_Rapida'), key=f"v_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with b2_col: pdia = st.selectbox("🌟 PD:", pilotos, index=get_idx('Piloto_Del_Dia'), key=f"p_{gp_sel}", placeholder="Elige...", disabled=bc or ya_aposto)
            with b3_col: ab = st.selectbox("💥 Abandono (Opcional):", pilotos, index=get_idx('Primer_Abandono'), key=f"a_{gp_sel}", placeholder="Ninguno", disabled=bc or ya_aposto)

            btn_disabled = ya_aposto or hay_error_q or hay_error_s or hay_error_c
            
            if st.button("🏎️ Sellar Apuesta", disabled=btn_disabled):
                campos_obligatorios = [q1, q2, q3, g1, g2, g3, vr, pdia]
                if es_sprint: campos_obligatorios += [s1, s2, s3]
                
                if None in campos_obligatorios: 
                    st.warning("⚠️ ¡Pits incompletos! Faltan pronósticos por llenar. El Bono Salado es el único opcional.")
                else:
                    v_s1, v_s2, v_s3 = s1 if s1 else "", s2 if s2 else "", s3 if s3 else ""
                    fila_guardar = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, v_s1, v_s2, v_s3, g1, g2, g3, vr, pdia, ab if ab else "", 0]
                    tabla_quinielas.append_row(fila_guardar)
                    st.success("✅ ¡Apuesta sellada con éxito!")
                    st.rerun()

    elif menu == "🏆 El Paddock":
        st.subheader("Clasificación Mundial del Campeonato")
        df_q = pd.DataFrame(tabla_quinielas.get_all_records())
        df_j = pd.DataFrame(tabla_jugadores.get_all_records())
        if not df_q.empty:
            df_q.columns = [str(c).strip() for c in df_q.columns]
            df_q['Puntos_Totales'] = pd.to_numeric(df_q.get('Puntos_Totales', 0), errors='coerce').fillna(0)
            res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index()
            if not df_j.empty:
                res = res.merge(df_j[['Nombre', 'Escuderia_Favorita']], left_on='Jugador', right_on='Nombre', how='left')
                res['🛡️'] = res['Escuderia_Favorita'].map(url_logos).fillna(url_logos["Cadillac"])
                res = res.rename(columns={'Jugador': 'Piloto', 'Escuderia_Favorita': 'Escudería', 'Puntos_Totales': 'Puntos'})
                res = res[['🛡️', 'Piloto', 'Escudería', 'Puntos']]
            else:
                res = res.rename(columns={'Jugador': 'Piloto', 'Puntos_Totales': 'Puntos'})
                
            res = res.sort_values('Puntos', ascending=False).reset_index(drop=True)
            
            html_table = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif;">'
            html_table += '<thead><tr style="background-color: #2e2e3e; color: white;">'
            html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">🛡️</th>'
            html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Piloto</th>'
            html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Escudería</th>'
            html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Puntos</th>'
            html_table += '</tr></thead><tbody>'
            for _, row in res.iterrows():
                logo_url = row.get('🛡️', '')
                img_tag = f'<img src="{logo_url}" width="30">' if logo_url else ''
                html_table += '<tr style="border-bottom: 1px solid #444; background-color: transparent;">'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{img_tag}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row["Piloto"]}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row.get("Escudería", "")}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle; font-weight: bold; font-size: 1.1rem;">{int(row["Puntos"])}</td>'
                html_table += '</tr>'
            html_table += '</tbody></table>'
            st.markdown(html_table, unsafe_allow_html=True)

    elif menu == "📊 Paddock Detallado":
        st.subheader("🔍 Análisis de Telemetría (Paddock Detallado)")
        df_q = pd.DataFrame(tabla_quinielas.get_all_records())
        if not df_q.empty:
            df_q.columns = [str(c).strip() for c in df_q.columns]
            op_v = st.selectbox("Ver:", ["🏆 Total"] + lista_carreras_oficial)
            if op_v == "🏆 Total":
                df_j = pd.DataFrame(tabla_jugadores.get_all_records())
                df_q['Puntos_Totales'] = pd.to_numeric(df_q.get('Puntos_Totales', 0), errors='coerce').fillna(0)
                res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index()
                
                if not df_j.empty:
                    res = res.merge(df_j[['Nombre', 'Escuderia_Favorita']], left_on='Jugador', right_on='Nombre', how='left')
                    res = res.rename(columns={'Jugador': 'Piloto', 'Escuderia_Favorita': 'Escudería', 'Puntos_Totales': 'Puntos'})
                    res = res[['Piloto', 'Escudería', 'Puntos']]
                else:
                    res = res.rename(columns={'Jugador': 'Piloto', 'Puntos_Totales': 'Puntos'})
                    
                res = res.sort_values('Puntos', ascending=False).reset_index(drop=True)
                
                html_table = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif;">'
                html_table += '<thead><tr style="background-color: #2e2e3e; color: white;">'
                html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Piloto</th>'
                html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Escudería</th>'
                html_table += '<th style="text-align:center; padding: 12px; border-bottom: 2px solid #E10600;">Puntos</th>'
                html_table += '</tr></thead><tbody>'
                for _, row in res.iterrows():
                    html_table += '<tr style="border-bottom: 1px solid #444; background-color: transparent;">'
                    html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row["Piloto"]}</td>'
                    html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row.get("Escudería", "")}</td>'
                    html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle; font-weight: bold; font-size: 1.1rem;">{int(row["Puntos"])}</td>'
                    html_table += '</tr>'
                html_table += '</tbody></table>'
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; margin: 10px 0px 20px 0px; font-size: 1.1rem; background-color: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #333;">
                    <span style="color: #00e676; font-weight: bold;">Verde +3</span> <span style="color: #666; margin: 0 10px;">|</span> 
                    <span style="color: #ffb300; font-weight: bold;">Amarillo +1</span> <span style="color: #666; margin: 0 10px;">|</span> 
                    <span style="color: #ff5252; font-weight: bold;">Rojo = 0</span> <span style="color: #666; margin: 0 10px;">|</span> 
                    <span style="color: gray; font-weight: bold;">Gris -2</span> <span style="color: #666; margin: 0 10px;">|</span> 
                    <span style="color: #FFD700; font-weight: bold; text-shadow: 1px 1px 2px #000;">Dorado +5</span>
                </div>
                """, unsafe_allow_html=True)

                df_f = df_q[df_q['Carrera'] == op_v].copy()
                
                f_cal = df_cal_global[df_cal_global['Carrera'] == op_v]
                es_sprint = False
                if not f_cal.empty:
                    if 'Es_Sprint' in f_cal.columns:
                        es_sprint = str(f_cal.iloc[0]['Es_Sprint']).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'S']

                if not df_f.empty:
                    def ac_n(n): return str(n).split()[-1] if (pd.notna(n) and " " in str(n)) else str(n)
                    todos_res = tabla_resultados.get_all_values()
                    r_of = {}
                    for fila in reversed(todos_res):
                        if len(fila) >= 13 and fila[0] == op_v:
                            r_of = {'Q1': ac_n(fila[1]), 'Q2': ac_n(fila[2]), 'Q3': ac_n(fila[3]), 'S1': ac_n(fila[4]), 'S2': ac_n(fila[5]), 'S3': ac_n(fila[6]), 'P1': ac_n(fila[7]), 'P2': ac_n(fila[8]), 'P3': ac_n(fila[9]), 'VR': ac_n(fila[10]), 'PD': ac_n(fila[11]), 'Salado': ac_n(fila[12])}
                            break
                    
                    df_f = df_f.rename(columns={"Qualy_P1":"Q1","Qualy_P2":"Q2","Qualy_P3":"Q3", "Sprint_P1":"S1", "Sprint_P2":"S2", "Sprint_P3":"S3", "Carrera_P1":"P1","Carrera_P2":"P2","Carrera_P3":"P3","Vuelta_Rapida":"VR","Piloto_Del_Dia":"PD","Primer_Abandono":"Salado","Puntos_Totales":"Pts"})
                    
                    columnas_renombrar = ["Q1","Q2","Q3","S1","S2","S3","P1","P2","P3","VR","PD","Salado"]
                    columnas_base = ["Q1","Q2","Q3","P1","P2","P3","VR","PD","Salado"]
                    
                    if es_sprint:
                        for c in columnas_renombrar: 
                            if c in df_f.columns: df_f[c] = df_f[c].apply(ac_n)
                    else:
                        for c in columnas_base: 
                            if c in df_f.columns: df_f[c] = df_f[c].apply(ac_n)
                    
                    rename_dict = {}
                    cols_iterar = ["Q1","Q2","Q3","S1","S2","S3","P1","P2","P3","VR","PD","Salado", "Pts"] if es_sprint else ["Q1","Q2","Q3","P1","P2","P3","VR","PD","Salado", "Pts"]
                    
                    for col in cols_iterar:
                        if col in r_of and r_of[col] != "": rename_dict[col] = f"{col}<br><span style='font-size:0.8rem; color:#aaa;'>({r_of[col]})</span>"
                        else: rename_dict[col] = col
                        
                    df_f = df_f.rename(columns=rename_dict)
                    cols_mostrar = ['Jugador'] + list(rename_dict.values())
                    df_mostrar = df_f[[c for c in cols_mostrar if c in df_f.columns]].copy()
                    
                    if list(rename_dict.values())[-1] in df_mostrar.columns:
                        col_pts = list(rename_dict.values())[-1]
                        df_mostrar[col_pts] = pd.to_numeric(df_mostrar[col_pts], errors='coerce').fillna(0)
                        df_mostrar = df_mostrar.sort_values(col_pts, ascending=False).reset_index(drop=True)
                    
                    html_det = '<table style="width:100%; text-align:center; border-collapse: collapse; font-family: sans-serif;">'
                    html_det += '<tr style="background-color: #2e2e3e; color: white;">'
                    for col in df_mostrar.columns:
                        html_det += f'<th style="text-align:center; padding: 10px; border-bottom: 2px solid #E10600; vertical-align: bottom;">{col}</th>'
                    html_det += '</tr>'

                    for _, row in df_mostrar.iterrows():
                        html_det += '<tr style="border-bottom: 1px solid #444;">'
                        for col in df_mostrar.columns:
                            val = str(row[col]).strip() if pd.notna(row[col]) else ""
                            inner_html = val
                            
                            if col != 'Jugador' and "Pts" not in col and r_of:
                                base = col.split('<br>')[0]
                                if val not in ["", "nan", "None", "🔒 CERRADO"]:
                                    if base == 'Salado':
                                        real = r_of.get('Salado', '')
                                        if val == real and real != "": inner_html = f'<span style="color: #FFD700; font-weight: bold; text-shadow: 1px 1px 2px #000;">{val}</span>'
                                        else: inner_html = f'<span style="color: gray; font-weight: bold;">{val}</span>'
                                    elif base in r_of:
                                        real = r_of[base]
                                        if val == real: inner_html = f'<span style="color: #00e676; font-weight: bold;">{val}</span>'
                                        elif base in ['P1','P2','P3', 'S1', 'S2', 'S3'] and val in [r_of.get(base[0]+'1'), r_of.get(base[0]+'2'), r_of.get(base[0]+'3')]: inner_html = f'<span style="color: #ffb300; font-weight: bold;">{val}</span>'
                                        elif base in ['Q1','Q2','Q3'] and val in [r_of.get('Q1'), r_of.get('Q2'), r_of.get('Q3')]: inner_html = f'<span style="color: #ffb300; font-weight: bold;">{val}</span>'
                                        else: inner_html = f'<span style="color: #ff5252; font-weight: bold;">{val}</span>'
                            elif "Pts" in col:
                                inner_html = f'<span style="font-weight: bold; font-size: 1.1rem;">{int(float(val)) if val != "" else 0}</span>'
                                
                            html_det += f'<td style="padding: 10px; vertical-align: middle; text-align:center;">{inner_html}</td>'
                        html_det += '</tr>'
                    html_det += '</table>'
                    st.markdown(html_det, unsafe_allow_html=True)

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos.")
        
        st.markdown("### 🎯 ARTÍCULO 2: Sistema de Puntuación Detallado")
        st.success("""
        Para las secciones de **Calificación (Q1, Q2, Q3)**, **Carrera (P1, P2, P3)** y **Carreras Sprint (S1, S2, S3)** el puntaje se calcula así:
        * 🥇 **Posición Exacta:** **+3 Puntos** si aciertas al piloto en el lugar exacto que pronosticaste.
        * 🥈 **Acierto Desordenado:** **+1 Punto** si tu piloto queda en el podio (Top 3 de esa sesión) pero en una posición distinta a la que elegiste.
        
        **Bonos Adicionales:**
        * 🚀 **Vuelta Rápida:** **+2 Puntos** por acierto exacto.
        * 🌟 **Piloto del Día:** **+2 Puntos** por acierto exacto.
        """)
        
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("""
        Esta apuesta es **OPCIONAL** (Puedes dejarla en 'Ninguno').
        * ✅ **Si Acertaste:** Si tu piloto es el primero en abandonar en la Carrera Principal, eres un genio del mal y te llevas **+5 Puntos** directos.
        * ❌ **Si Fallaste:** Si sobrevive o alguien más abandona antes, la FIA te castiga con **-2 Puntos**.
        """)
        
        st.markdown("### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
        st.error("Los resultados son inyectados directamente por la telemetría oficial de la API y validados por el mismísimo **Sasian**. La decisión final es absoluta e inapelable.")

    elif menu == "👑 Admin FIA":
        sel_car = st.selectbox("Gran Premio a Dictaminar:", lista_carreras_oficial)
        f_cal = df_cal_global[df_cal_global['Carrera'] == sel_car]
        es_sprint = False
        if not f_cal.empty:
            if 'Es_Sprint' in f_cal.columns:
                es_sprint = str(f_cal.iloc[0]['Es_Sprint']).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'S']
        
        todos_resultados = tabla_resultados.get_all_values()
        res_previos = {}
        for fila in reversed(todos_resultados):
            if len(fila) >= 13 and fila[0] == sel_car:
                res_previos = {
                    'rq1': fila[1], 'rq2': fila[2], 'rq3': fila[3],
                    'rs1': fila[4], 'rs2': fila[5], 'rs3': fila[6],
                    'rg1': fila[7], 'rg2': fila[8], 'rg3': fila[9],
                    'rvr': fila[10], 'rpd': fila[11], 'rab': fila[12]
                }
                break

        if res_previos:
            st.info("💡 Ya hay resultados oficiales guardados para esta carrera.")

        def get_idx_res(llave, d_v=None):
            if res_previos and llave in res_previos and res_previos[llave] in pilotos: 
                return pilotos.index(res_previos[llave])
            if d_v in pilotos: 
                return pilotos.index(d_v)
            return None

        if st.button("⚡ Cargar API"):
            try:
                r = requests.get("https://api.jolpi.ca/ergast/f1/current/last/results.json").json()
                res_api = r['MRData']['RaceTable']['Races'][0]['Results']
                st.session_state['auto_c1'] = traductor_api.get(res_api[0]['Driver']['familyName']); st.session_state['auto_c2'] = traductor_api.get(res_api[1]['Driver']['familyName']); st.session_state['auto_c3'] = traductor_api.get(res_api[2]['Driver']['familyName'])
                st.success("API cargada.")
            except: st.error("Error API.")

        with st.form("fia"):
            c1, c2, c3 = st.columns(3)
            with c1: rq1 = st.selectbox("Q1:", pilotos, index=get_idx_res('rq1'), placeholder="Elige...")
            with c2: rq2 = st.selectbox("Q2:", pilotos, index=get_idx_res('rq2'), placeholder="Elige...")
            with c3: rq3 = st.selectbox("Q3:", pilotos, index=get_idx_res('rq3'), placeholder="Elige...")
            
            if es_sprint:
                s1_c, s2_c, s3_c = st.columns(3)
                with s1_c: rs1 = st.selectbox("Sprint P1:", pilotos, index=get_idx_res('rs1'), placeholder="Elige...")
                with s2_c: rs2 = st.selectbox("Sprint P2:", pilotos, index=get_idx_res('rs2'), placeholder="Elige...")
                with s3_c: rs3 = st.selectbox("Sprint P3:", pilotos, index=get_idx_res('rs3'), placeholder="Elige...")
            else:
                rs1, rs2, rs3 = "", "", ""
                
            c1_c, c2_c, c3_c = st.columns(3)
            with c1_c: rg1 = st.selectbox("Carrera P1:", pilotos, index=get_idx_res('rg1', st.session_state.get('auto_c1')), placeholder="Elige...")
            with c2_c: rg2 = st.selectbox("Carrera P2:", pilotos, index=get_idx_res('rg2', st.session_state.get('auto_c2')), placeholder="Elige...")
            with c3_c: rg3 = st.selectbox("Carrera P3:", pilotos, index=get_idx_res('rg3', st.session_state.get('auto_c3')), placeholder="Elige...")
            
            b1, b2, b3 = st.columns(3)
            with b1: rvr = st.selectbox("VR:", pilotos, index=get_idx_res('rvr'), placeholder="Elige...")
            with b2: rpd = st.selectbox("PD:", pilotos, index=get_idx_res('rpd'), placeholder="Elige...")
            with b3: abr = st.selectbox("Abandono:", pilotos, index=get_idx_res('rab'), placeholder="Ninguno")
            
            if st.form_submit_button("⚖️ Repartir Puntos"):
                v_rq1, v_rq2, v_rq3 = rq1 if rq1 else "", rq2 if rq2 else "", rq3 if rq3 else ""
                v_rs1, v_rs2, v_rs3 = rs1 if rs1 else "", rs2 if rs2 else "", rs3 if rs3 else ""
                v_rg1, v_rg2, v_rg3 = rg1 if rg1 else "", rg2 if rg2 else "", rg3 if rg3 else ""
                v_rvr, v_rpd, v_abr = rvr if rvr else "", rpd if rpd else "", abr if abr else ""

                tabla_resultados.append_row([sel_car, v_rq1, v_rq2, v_rq3, v_rs1, v_rs2, v_rs3, v_rg1, v_rg2, v_rg3, v_rvr, v_rpd, v_abr])
                
                df_q = pd.DataFrame(tabla_quinielas.get_all_records())
                headers_q = tabla_quinielas.row_values(1)
                headers_q = [str(h).strip() for h in headers_q]
                
                if 'Puntos_Totales' in headers_q:
                    col_pts_idx = headers_q.index('Puntos_Totales') + 1
                    celdas = []
                    
                    podio_q = [v_rq1, v_rq2, v_rq3]
                    podio_s = [v_rs1, v_rs2, v_rs3]
                    podio_c = [v_rg1, v_rg2, v_rg3]
                    
                    for i, row in df_q.iterrows():
                        if str(row.get('Carrera', '')).strip() == sel_car.strip():
                            p = 0
                            
                            ap_q = [str(row.get('Qualy_P1','')), str(row.get('Qualy_P2','')), str(row.get('Qualy_P3',''))]
                            for j, ap in enumerate(ap_q): 
                                if ap == podio_q[j] and ap != "": p += 3
                                elif ap in podio_q and ap != "": p += 1
                                
                            if es_sprint:
                                ap_s = [str(row.get('Sprint_P1','')), str(row.get('Sprint_P2','')), str(row.get('Sprint_P3',''))]
                                for j, ap in enumerate(ap_s): 
                                    if ap == podio_s[j] and ap != "": p += 3
                                    elif ap in podio_s and ap != "": p += 1
                            
                            ap_c = [str(row.get('Carrera_P1','')), str(row.get('Carrera_P2','')), str(row.get('Carrera_P3',''))]
                            for j, ap in enumerate(ap_c): 
                                if ap == podio_c[j] and ap != "": p += 3
                                elif ap in podio_c and ap != "": p += 1
                            
                            if str(row.get('Vuelta_Rapida','')) == v_rvr and v_rvr != "": p += 2
                            if str(row.get('Piloto_Del_Dia','')) == v_rpd and v_rpd != "": p += 2
                            
                            v_ab_jugador = str(row.get('Primer_Abandono',''))
                            if v_ab_jugador != "" and v_ab_jugador != "🔒 CERRADO":
                                if v_abr and v_ab_jugador == v_abr: p += 5
                                else: p -= 2
                                
                            celdas.append(gspread.Cell(row=i+2, col=col_pts_idx, value=p))
                    
                    if celdas: tabla_quinielas.update_cells(celdas)
                    st.success("🏆 ¡Actualizado al milímetro con el formato Sprint!")
                else:
                    st.error("Error: No encontré la columna 'Puntos_Totales' en Quinielas.")
