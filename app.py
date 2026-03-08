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

    st.markdown("""<div style="text-align: center; background: #1e1e1e; padding: 10px; border-radius: 12px; border-bottom: 4px solid #E10600;"><span style="font-family: Impact; font-size: 3rem; color: #E10600; font-style: italic;">F1 SasianGP</span></div>""", unsafe_allow_html=True)

    if menu == "📝 Hacer Apuesta":
        gp_sel = st.selectbox("🌎 Selecciona GP:", lista_carreras_oficial, index=None)
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
            filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
            ya_aposto, ap_p = not filtro.empty, filtro.iloc[-1].to_dict() if not filtro.empty else {}
            if ya_aposto: st.info("💡 Parque Cerrado activo.")

            def get_idx(campo): return pilotos.index(ap_p.get(campo)) if ya_aposto and ap_p.get(campo) in pilotos else None

            st.markdown("### ⏱️ Calificación")
            q1 = st.selectbox("Q1:", pilotos, index=get_idx('Qualy_P1'), key=f"q1_{gp_sel}", disabled=bq or ya_aposto)
            q2 = st.selectbox("Q2:", pilotos, index=get_idx('Qualy_P2'), key=f"q2_{gp_sel}", disabled=bq or ya_aposto)
            q3 = st.selectbox("Q3:", pilotos, index=get_idx('Qualy_P3'), key=f"q3_{gp_sel}", disabled=bq or ya_aposto)
            st.markdown("### 🏁 Carrera")
            g1 = st.selectbox("P1:", pilotos, index=get_idx('Carrera_P1'), key=f"g1_{gp_sel}", disabled=bc or ya_aposto)
            g2 = st.selectbox("P2:", pilotos, index=get_idx('Carrera_P2'), key=f"g2_{gp_sel}", disabled=bc or ya_aposto)
            g3 = st.selectbox("P3:", pilotos, index=get_idx('Carrera_P3'), key=f"g3_{gp_sel}", disabled=bc or ya_aposto)
            vr = st.selectbox("🚀 VR:", pilotos, index=get_idx('Vuelta_Rapida'), key=f"v_{gp_sel}", disabled=bc or ya_aposto)
            pdia = st.selectbox("🌟 PD:", pilotos, index=get_idx('Piloto_Del_Dia'), key=f"p_{gp_sel}", disabled=bc or ya_aposto)
            ab = st.selectbox("💥 Abandono:", pilotos, index=get_idx('Primer_Abandono'), key=f"a_{gp_sel}", placeholder="Ninguno", disabled=bc or ya_aposto)

            if st.button("🏎️ Sellar Apuesta", disabled=ya_aposto):
                if None in [q1, q2, q3, g1, g2, g3, vr, pdia]: st.warning("⚠️ Incompleto.")
                elif len(set([q1, q2, q3])) < 3 or len(set([g1, g2, g3])) < 3: st.error("❌ Repetidos.")
                else:
                    tabla_quinielas.append_row([(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), st.session_state['usuario_activo'], gp_sel, q1, q2, q3, g1, g2, g3, vr, pdia, ab if ab else "", 0])
                    st.success("✅ Sellado.")
                    st.rerun()

    elif menu == "📊 Paddock Detallado":
        df_q = pd.DataFrame(tabla_quinielas.get_all_records())
        if not df_q.empty:
            op_v = st.selectbox("Ver:", ["🏆 Total"] + lista_carreras_oficial)
            if op_v == "🏆 Total":
                st.dataframe(df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index().sort_values('Puntos_Totales', ascending=False), use_container_width=True)
            else:
                df_f = df_q[df_q['Carrera'] == op_v].copy()
                if not df_f.empty:
                    def ac_n(n): return str(n).split()[-1] if (pd.notna(n) and " " in str(n)) else str(n)
                    todos_res = tabla_resultados.get_all_values()
                    r_of = {}
                    for fila in reversed(todos_res):
                        if len(fila) >= 10 and fila[0] == op_v:
                            r_of = {'Q1': ac_n(fila[1]), 'Q2': ac_n(fila[2]), 'Q3': ac_n(fila[3]), 'P1': ac_n(fila[4]), 'P2': ac_n(fila[5]), 'P3': ac_n(fila[6]), 'VR': ac_n(fila[7]), 'PD': ac_n(fila[8]), 'Salado': ac_n(fila[9])}
                            break
                    df_f = df_f.rename(columns={"Qualy_P1":"Q1","Qualy_P2":"Q2","Qualy_P3":"Q3","Carrera_P1":"P1","Carrera_P2":"P2","Carrera_P3":"P3","Vuelta_Rapida":"VR","Piloto_Del_Dia":"PD","Primer_Abandono":"Salado","Puntos_Totales":"Pts"})
                    for c in ["Q1","Q2","Q3","P1","P2","P3","VR","PD","Salado"]: df_f[c] = df_f[c].apply(ac_n)
                    def style_txt(row):
                        styles = [''] * len(row)
                        for i, col in enumerate(row.index):
                            if col in ['Jugador', 'Pts'] or not r_of: continue
                            val = str(row[col]).strip()
                            if val in ["", "nan", "None"]: continue
                            if col in r_of:
                                real = r_of[col]
                                if val == real: styles[i] = 'color: #00e676; font-weight: bold;'
                                elif col in ['P1','P2','P3'] and val in [r_of['P1'], r_of['P2'], r_of['P3']]: styles[i] = 'color: #ffb300; font-weight: bold;'
                                elif col in ['Q1','Q2','Q3'] and val in [r_of['Q1'], r_of['Q2'], r_of['Q3']]: styles[i] = 'color: #ffb300; font-weight: bold;'
                                else: styles[i] = 'color: #ff5252; font-weight: bold;'
                        return styles
                    st.dataframe(df_f[['Jugador','Q1','Q2','Q3','P1','P2','P3','VR','PD','Salado','Pts']].style.apply(style_txt, axis=1), use_container_width=True, hide_index=True)

    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona")
        st.info("Pits cierran 1 hora antes de Qualy y 1 hora antes de Carrera.")
        st.markdown("### 🎯 ARTÍCULO 2: Sistema de Puntuación Detallado")
        st.success("""
        **Calificación (Q1-Q3) y Carrera (P1-P3):**
        * 🥇 **Posición Exacta:** **+3 Puntos**.
        * 🥈 **Acierto Desordenado:** **+1 Punto** si tu piloto queda en el podio (Top 3) pero en otra posición.
        
        **Bonos:**
        * 🚀 **Vuelta Rápida:** **+2 Puntos**.
        * 🌟 **Piloto del Día:** **+2 Puntos**.
        """)
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("⚠️ **Opcional:** **+5 Puntos** si aciertas el primer abandono / **-5 Puntos** si fallas.")

    elif menu == "👑 Admin FIA":
        sel_car = st.selectbox("Carrera:", lista_carreras_oficial)
        if st.button("⚡ API"):
            try:
                r = requests.get("https://api.jolpi.ca/ergast/f1/current/last/results.json").json()
                res_api = r['MRData']['RaceTable']['Races'][0]['Results']
                st.session_state['auto_c1'] = traductor_api.get(res_api[0]['Driver']['familyName']); st.session_state['auto_c2'] = traductor_api.get(res_api[1]['Driver']['familyName']); st.session_state['auto_c3'] = traductor_api.get(res_api[2]['Driver']['familyName'])
                st.success("API cargada.")
            except: st.error("Error API.")
        with st.form("fia"):
            cq1, cq2, cq3 = st.columns(3); rq1 = cq1.selectbox("Q1:", pilotos); rq2 = cq2.selectbox("Q2:", pilotos); rq3 = cq3.selectbox("Q3:", pilotos)
            cp1, cp2, cp3 = st.columns(3); rg1 = cp1.selectbox("P1:", pilotos, index=pilotos.index(st.session_state.get('auto_c1')) if st.session_state.get('auto_c1') in pilotos else None); rg2 = cp2.selectbox("P2:", pilotos, index=pilotos.index(st.session_state.get('auto_c2')) if st.session_state.get('auto_c2') in pilotos else None); rg3 = cp3.selectbox("P3:", pilotos, index=pilotos.index(st.session_state.get('auto_c3')) if st.session_state.get('auto_c3') in pilotos else None)
            vrr = st.selectbox("VR:", pilotos); pdd = st.selectbox("PD:", pilotos); abr = st.selectbox("Abandono:", pilotos, index=None)
            if st.form_submit_button("⚖️ Repartir Puntos"):
                tabla_resultados.append_row([sel_car, rq1, rq2, rq3, rg1, rg2, rg3, vrr, pdd, abr if abr else ""])
                celdas = []; t_q = tabla_quinielas.get_all_values()
                podio_c = [rg1, rg2, rg3]; podio_q = [rq1, rq2, rq3]
                for idx, fila in enumerate(t_q[1:], start=2):
                    fila += [""] * (13 - len(fila))
                    if fila[2] == sel_car:
                        p = 0
                        for i, a in enumerate([fila[6], fila[7], fila[8]]): 
                            if a == podio_c[i]: p += 3
                            elif a in podio_c and a != "": p += 1
                        for i, a in enumerate([fila[3], fila[4], fila[5]]):
                            if a == podio_q[i]: p += 3
                            elif a in podio_q and a != "": p += 1
                        if fila[9] == vrr and vrr != "": p += 2
                        if fila[10] == pdd and pdd != "": p += 2
                        if fila[11] != "":
                            if fila[11] == abr: p += 5
                            else: p -= 5
                        celdas.append(gspread.Cell(row=idx, col=13, value=p))
                if celdas: tabla_quinielas.update_cells(celdas)
                st.success("🏆 Actualizado.")
