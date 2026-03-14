import json
import streamlit as st
import gspread
from datetime import datetime, timedelta, date
import pandas as pd
import requests
import time
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_cookies_controller import CookieController
import os

# --- 1. CONFIGURACIÓN VISUAL FORZADA ---
try:
    img_icono = Image.open("icono.jpg")
    st.set_page_config(page_title="SasianGP 2026 - CAMPEONATOS PRIVADOS", page_icon=img_icono, layout="wide") 
except FileNotFoundError:
    st.set_page_config(page_title="SasianGP 2026 - CAMPEONATOS PRIVADOS", page_icon="🏎️", layout="wide")

# --- AQUÍ PRENDEMOS EL HORNO DE GALLETAS ---
controller = CookieController()

# --- TRUCO SUCIO PARA EL IPHONE ---
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://github.com/Sasian24/Formula1/blob/main/icono.png?raw=true">
    </head>
    """,
    unsafe_allow_html=True
)

# --- 2. CONEXIÓN A BASE DE DATOS (ANTICOLAPSO V2) ---
@st.cache_resource
def init_gspread():
    caja_fuerte = st.secrets["gcp_json"]
    cred_dict = json.loads(caja_fuerte)
    
    gc = gspread.service_account_from_dict(cred_dict)
    sh = gc.open("SasianGP_DB")
    return (
        sh.worksheet("Quinielas"),
        sh.worksheet("Jugadores"),
        sh.worksheet("Resultados"),
        sh.worksheet("Calendario"),
        sh.worksheet("Campeonatos_Admin"),
        sh.worksheet("Solicitudes"),
        sh.worksheet("Mensajes"),
        sh
    )

tabla_quinielas, tabla_jugadores, tabla_resultados, tabla_calendario, tabla_campeonatos_admin, tabla_solicitudes, tabla_mensajes, sh_completa = init_gspread()

@st.cache_data(ttl=60)
def fetch_data_jugadores(): return pd.DataFrame(tabla_jugadores.get_all_records())

@st.cache_data(ttl=60)
def fetch_data_quinielas(): return pd.DataFrame(tabla_quinielas.get_all_records())

@st.cache_data(ttl=600)
def fetch_data_calendario():
    try:
        data = tabla_calendario.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error al conectar con la pestaña 'Calendario': {e}")
        return pd.DataFrame()

df_cal_global = fetch_data_calendario()

@st.cache_data(ttl=60)
def fetch_vals_resultados(): return tabla_resultados.get_all_values()

@st.cache_data(ttl=30)
def fetch_data_campeonatos_admin(): return pd.DataFrame(tabla_campeonatos_admin.get_all_records())

@st.cache_data(ttl=30)
def fetch_data_solicitudes(): return pd.DataFrame(tabla_solicitudes.get_all_records())

@st.cache_data(ttl=30)
def fetch_data_mensajes(): return pd.DataFrame(tabla_mensajes.get_all_records())

# --- 3. LOGOS Y PILOTOS ---
url_logos = {
    "red bull racing": "https://raw.githubusercontent.com/Sasian24/Formula1/main/red_bull.png",
    "ferrari": "https://raw.githubusercontent.com/Sasian24/Formula1/main/ferrari.png",
    "mercedes": "https://raw.githubusercontent.com/Sasian24/Formula1/main/mercedes.png",
    "mclaren": "https://raw.githubusercontent.com/Sasian24/Formula1/main/mclaren.png",
    "aston martin": "https://raw.githubusercontent.com/Sasian24/Formula1/main/aston_martin.png",
    "alpine": "https://raw.githubusercontent.com/Sasian24/Formula1/main/alpine.png",
    "racing bulls": "https://raw.githubusercontent.com/Sasian24/Formula1/main/racing_bulls.png",
    "audi": "https://raw.githubusercontent.com/Sasian24/Formula1/main/audi.png",
    "haas": "https://raw.githubusercontent.com/Sasian24/Formula1/main/haas.png",
    "cadillac": "https://raw.githubusercontent.com/Sasian24/Formula1/main/cadillac.png"
}

pilotos = sorted([
    "Checo Pérez", "Max Verstappen", "Charles Leclerc", "Lewis Hamilton", 
    "Lando Norris", "Oscar Piastri", "George Russell", "Fernando Alonso", 
    "Carlos Sainz", "Franco Colapinto", "Nico Hülkenberg", "Esteban Ocon", 
    "Pierre Gasly", "Alex Albon", "Lance Stroll", "Valtteri Bottas",
    "Arvid Lindblad", "Isack Hadjar", "Kimi Antonelli", "Oliver Bearman", 
    "Liam Lawson", "Gabriel Bortoleto"
])

if not df_cal_global.empty: df_cal_global.columns = [str(c).strip() for c in df_cal_global.columns]
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
galleta_usuario = controller.get('SasianGP_Piloto')

if galleta_usuario and 'usuario_activo' not in st.session_state:
    st.session_state['usuario_activo'] = galleta_usuario

if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'campeonato_activo' not in st.session_state: st.session_state['campeonato_activo'] = None
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
            df_j = fetch_data_jugadores()
            user_match = df_j[(df_j['Nombre']==u.strip()) & (df_j['Password']==p.strip())]
            if not user_match.empty:
                st.session_state['usuario_activo'] = u.strip()
                controller.set('SasianGP_Piloto', u.strip(), max_age=31536000) 
                campeonatos_usuario = str(user_match.iloc[0].get('Campeonato', '')).strip().split(',')
                st.session_state['campeonato_activo'] = campeonatos_usuario[0].strip() if campeonatos_usuario[0] else "Sin Campeonato"
                st.success("✅ ¡Semáforo en verde! Entrando al Paddock...")
                time.sleep(1)
                st.rerun()
            else: st.error("❌ Acceso Denegado.")
            
    with tab2:
        nu = st.text_input("Alias *", key="r_u")
        np = st.text_input("Contraseña *", type="password", key="r_p")
        
        df_la = fetch_data_campeonatos_admin()
        campeonatos_existentes = sorted([str(l).strip() for l in df_la['Nombre_Campeonato'].unique() if str(l).strip() != ""]) if not df_la.empty else []
            
        opciones_camp = campeonatos_existentes + ["Otro (Crear Nuevo)"]
        n_camp_sel = st.selectbox("Selecciona tu Campeonato *", opciones_camp, index=None, placeholder="Elige el campeonato de tus amigos...")
        
        n_camp_final = st.text_input("Nombre de tu Nuevo Campeonato *", key="r_camp_nuevo").strip() if n_camp_sel == "Otro (Crear Nuevo)" else n_camp_sel

        wp = st.text_input("WhatsApp", key="r_w")
        mail = st.text_input("Correo *", key="r_m")
        cumple = st.date_input("Cumpleaños (DD/MM/YYYY)", value=None, min_value=date(1930, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        pil_f = st.selectbox("Piloto Favorito", pilotos, index=None)
        esc = st.selectbox("Escudería *", list(url_logos.keys()))
        
        if st.button("✍️ Firmar Contrato"):
            if not nu or not np or not esc or not n_camp_final or not mail:
                st.error("⚠️ Llena todos los campos obligatorios (*).")
            else:
                ahora_mx = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
                fecha_guardar = cumple.strftime("%d/%m/%Y") if cumple else ""
                
                if n_camp_sel == "Otro (Crear Nuevo)":
                    tabla_jugadores.append_row([ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), fecha_guardar, pil_f if pil_f else "", "", esc, n_camp_final])
                    tabla_campeonatos_admin.append_row([n_camp_final, nu.strip()])
                    st.cache_data.clear()
                    st.session_state['usuario_activo'] = nu.strip()
                    st.session_state['campeonato_activo'] = n_camp_final
                    st.success(f"✅ ¡Campeonato '{n_camp_final}' creado! Eres el Comisario oficial.")
                    st.rerun()
                else:
                    tabla_jugadores.append_row([ahora_mx, nu.strip(), np.strip(), wp.strip(), mail.strip(), fecha_guardar, pil_f if pil_f else "", "", esc, ""])
                    tabla_solicitudes.append_row([nu.strip(), n_camp_final, "Pendiente"])
                    st.cache_data.clear()
                    st.warning(f"⏳ ¡Contrato firmado! El acceso al campeonato '{n_camp_final}' requiere aprobación. Espera a que el Comisario te acepte.")
                
    with tab3:
        uo = st.text_input("Alias para recuperar:", key="f_u")
        if st.button("✉️ Enviar Clave al Correo"):
            df_j = fetch_data_jugadores()
            match = df_j[df_j['Nombre'] == uo.strip()]
            
            if not match.empty:
                correo_destino = str(match.iloc[0].get('Correo', '')).strip()
                password_usuario = str(match.iloc[0]['Password'])
                
                if correo_destino and correo_destino != "nan" and correo_destino != "":
                    correo_escuderia = "rsasian.qwerty@gmail.com" 
                    password_app = "pkfosnupqdlmfrox"
                    
                    msg = MIMEMultipart()
                    msg['From'] = correo_escuderia
                    msg['To'] = correo_destino
                    msg['Subject'] = "🏎️ Recuperación de Clave - SasianGP 2026"
                    
                    cuerpo = f"Hola Piloto {uo.strip()},\n\nAlguien solicitó la clave de acceso para tu monoplaza.\nTu contraseña secreta es: {password_usuario}\n\n¡Nos vemos en la pista de SasianGP!"
                    msg.attach(MIMEText(cuerpo, 'plain'))
                    
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(correo_escuderia, password_app)
                        texto = msg.as_string()
                        server.sendmail(correo_escuderia, correo_destino, texto)
                        server.quit()
                        st.success("✅ ¡Bandera Verde! La clave fue enviada al correo registrado de este piloto.")
                    except Exception as e:
                        st.error(f"❌ Falla de motor. Detalle técnico: {e}")
                else:
                    st.error("⚠️ Este piloto no tiene un correo registrado en la base de datos.")
            else: 
                st.error("❌ Piloto no encontrado en el Paddock.")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    df_admin = fetch_data_campeonatos_admin()
    mis_campeonatos_admin = df_admin[df_admin['Creador'] == st.session_state['usuario_activo']]['Nombre_Campeonato'].tolist() if not df_admin.empty else []
    es_admin_fia = str(st.session_state['usuario_activo']).strip().lower() == "sasian"
    
    df_j_full = fetch_data_jugadores()
    match_usr = df_j_full[df_j_full['Nombre'] == st.session_state['usuario_activo']]
    mis_camps = []
    if not match_usr.empty:
        camps_str = str(match_usr.iloc[0].get('Campeonato', '')).strip()
        mis_camps = [c.strip() for c in camps_str.split(',') if c.strip() != ""]
    
    if not mis_camps: mis_camps = ["Sin Campeonato"]
    if st.session_state['campeonato_activo'] not in mis_camps: st.session_state['campeonato_activo'] = mis_camps[0]
    
    with st.sidebar:
        st.markdown(f"### 🏎️ Pits: {st.session_state['usuario_activo']}")
        
        camp_sel = st.selectbox("🏆 Viendo Campeonato:", mis_camps, index=mis_camps.index(st.session_state['campeonato_activo']))
        if camp_sel != st.session_state['campeonato_activo']:
            st.session_state['campeonato_activo'] = camp_sel
            st.rerun()

        with st.expander("➕ Unirme o Crear Campeonato"):
            df_todas = fetch_data_campeonatos_admin()
            todos_los_camps = sorted([str(l).strip() for l in df_todas['Nombre_Campeonato'].unique() if str(l).strip() != ""]) if not df_todas.empty else []
            camps_disponibles = [c for c in todos_los_camps if c not in mis_camps and c != "Sin Campeonato"]
            
            op_camp = st.radio("¿Qué deseas hacer?", ["🤝 Unirme a uno existente", "🌟 Crear uno nuevo"])
            
            if op_camp == "🤝 Unirme a uno existente":
                if camps_disponibles:
                    sol_camp = st.selectbox("Selecciona el campeonato:", camps_disponibles, index=None, placeholder="Elige uno...")
                    if st.button("Enviar Solicitud"):
                        if sol_camp:
                            tabla_solicitudes.append_row([st.session_state['usuario_activo'], sol_camp.strip(), "Pendiente"])
                            st.cache_data.clear()
                            st.success(f"✅ Solicitud enviada al Comisario de {sol_camp}.")
                        else: st.warning("⚠️ Selecciona un campeonato primero.")
                else:
                    st.info("🏁 Ya eres miembro de todos los campeonatos disponibles.")
            
            elif op_camp == "🌟 Crear uno nuevo":
                n_camp_nuevo = st.text_input("Nombre de tu nuevo campeonato:")
                if st.button("Crear y Entrar"):
                    if n_camp_nuevo:
                        tabla_campeonatos_admin.append_row([n_camp_nuevo.strip(), st.session_state['usuario_activo']])
                        df_j = fetch_data_jugadores()
                        idx_jug = df_j.index[df_j['Nombre'] == st.session_state['usuario_activo']].tolist()
                        if idx_jug:
                            f_jug = idx_jug[0] + 2
                            camp_actual = str(df_j.at[idx_jug[0], 'Campeonato']).strip()
                            camp_final = f"{camp_actual}, {n_camp_nuevo.strip()}" if camp_actual and camp_actual != "Sin Campeonato" else n_camp_nuevo.strip()
                            tabla_jugadores.update_cell(f_jug, 10, camp_final)
                        st.cache_data.clear()
                        st.session_state['campeonato_activo'] = n_camp_nuevo.strip()
                        st.success(f"✅ ¡Campeonato '{n_camp_nuevo}' creado! Eres el Comisario oficial.")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.warning("⚠️ Necesitas escribir un nombre para el campeonato.")

        with st.expander("👤 Editar Mi Perfil"):
            df_j_perfil = fetch_data_jugadores()
            match_usr_perfil = df_j_perfil[df_j_perfil['Nombre'] == st.session_state['usuario_activo']]

            if not match_usr_perfil.empty:
                idx_jug_p = match_usr_perfil.index[0]
                fila_excel_p = int(idx_jug_p) + 2

                correo_actual = str(match_usr_perfil.iloc[0].get('Correo', '')).strip()
                wp_actual = str(match_usr_perfil.iloc[0].get('WhatsApp', '')).strip()
                pass_actual = str(match_usr_perfil.iloc[0].get('Password', '')).strip()
                piloto_actual = str(match_usr_perfil.iloc[0].get('Piloto_Favorito', '')).strip()
                escu_actual = str(match_usr_perfil.iloc[0].get('Escuderia_Favorita', '')).strip().lower()

                idx_piloto = pilotos.index(piloto_actual) if piloto_actual in pilotos else None
                claves_escuderias = list(url_logos.keys())
                idx_escu = claves_escuderias.index(escu_actual) if escu_actual in claves_escuderias else None

                with st.form("form_perfil_sidebar"):
                    n_correo = st.text_input("Correo:", value=correo_actual if correo_actual != "nan" else "")
                    n_wp = st.text_input("WhatsApp:", value=wp_actual if wp_actual != "nan" else "")
                    n_pass = st.text_input("Contraseña:", value=pass_actual, type="password")
                    n_piloto = st.selectbox("Piloto Favorito:", pilotos, index=idx_piloto, placeholder="Elige...")
                    n_escu = st.selectbox("Escudería:", claves_escuderias, index=idx_escu)
                    
                    if st.form_submit_button("💾 Guardar"):
                        if not n_correo or not n_escu:
                            st.error("⚠️ Correo y escudería requeridos.")
                        else:
                            celdas_actualizar = [
                                gspread.Cell(row=fila_excel_p, col=3, value=n_pass.strip()),
                                gspread.Cell(row=fila_excel_p, col=4, value=n_wp.strip()),
                                gspread.Cell(row=fila_excel_p, col=5, value=n_correo.strip()),
                                gspread.Cell(row=fila_excel_p, col=7, value=n_piloto if n_piloto else ""),
                                gspread.Cell(row=fila_excel_p, col=9, value=n_escu)
                            ]
                            tabla_jugadores.update_cells(celdas_actualizar)
                            st.cache_data.clear()
                            st.success("✅ Actualizado")
                            time.sleep(1)
                            st.rerun()
            else:
                st.error("❌ Datos no encontrados.")

        st.markdown("---")
        opciones_nav = ["🏆 El Paddock", "📊 Paddock Detallado", "📝 Hacer Apuesta", "🌍 Campeonato Real F1", "📖 Reglamento Oficial", "📘 Manual del Piloto"]
        if mis_campeonatos_admin: opciones_nav.append("🛡️ Administrar mis Campeonatos")
        if es_admin_fia: opciones_nav.append("👑 Admin FIA")
        
        menu = st.radio("Navegación", opciones_nav)
        
        st.markdown("---")
        if st.button("🚪 Salir de los Pits"):
            controller.remove('SasianGP_Piloto')
            st.session_state['usuario_activo'] = None
            st.session_state['campeonato_activo'] = None
            st.rerun()

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
    
    # --- SISTEMA DE MENSAJES GLOBALES (ANIMADO) ---
    df_msg = fetch_data_mensajes()
    if not df_msg.empty:
        msg_texto = str(df_msg.iloc[0].get('Aviso', '')).strip()
        msg_tipo = str(df_msg.iloc[0].get('Tipo', 'Informativo')).strip()
        
        if msg_texto and msg_texto != "nan":
            colores = {
                "Crítico": "background-color: #E10600; color: white;", 
                "Alerta": "background-color: #FFC107; color: black;", 
                "Éxito": "background-color: #00e676; color: black;",  
                "Informativo": "background-color: #2196F3; color: white;" 
            }
            iconos = {"Crítico": "🚨", "Alerta": "🟡", "Éxito": "🟢", "Informativo": "🔵"}
            
            estilo = colores.get(msg_tipo, colores["Informativo"])
            icono = iconos.get(msg_tipo, iconos["Informativo"])
            
            html_ticker = f"""
            <div style="{estilo} padding: 10px; border-radius: 8px; font-weight: bold; font-size: 1.2rem; margin-bottom: 15px; border: 1px solid #444;">
                <marquee behavior="scroll" direction="left" scrollamount="10">
                    {icono} <strong>DIRECCIÓN DE CARRERA:</strong> {msg_texto} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {icono} <strong>DIRECCIÓN DE CARRERA:</strong> {msg_texto}
                </marquee>
            </div>
            """
            st.markdown(html_ticker, unsafe_allow_html=True)

    if st.session_state['campeonato_activo'] == "Sin Campeonato":
        st.error("🚨 Estás en la sala de espera. Un Comisario debe aprobar tu solicitud antes de poder entrar al Paddock.")
    
    # --- MENÚ: ADMINISTRAR CAMPEONATOS ---
    elif menu == "🛡️ Administrar mis Campeonatos":
        st.header("🛡️ Control de Pases VIP (Cadenero)")
        st.write("Como creador del campeonato, aquí decides quién entra a tu Paddock.")
        
        df_sol = fetch_data_solicitudes()
        if not df_sol.empty:
            pendientes = df_sol[(df_sol['Campeonato_Deseado'].isin(mis_campeonatos_admin)) & (df_sol['Estatus'] == 'Pendiente')]
            if pendientes.empty: st.success("✅ Pista limpia. No hay solicitudes pendientes por revisar.")
            else:
                for idx_df, row in pendientes.iterrows():
                    fila_excel = idx_df + 2 
                    with st.container():
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.info(f"🏎️ El piloto **{row['Jugador']}** solicita unirse a **{row['Campeonato_Deseado']}**.")
                        if c2.button("✅ Aprobar", key=f"ok_{idx_df}"):
                            tabla_solicitudes.update_cell(fila_excel, 3, "Aprobado")
                            df_j = fetch_data_jugadores()
                            idx_jug = df_j.index[df_j['Nombre'] == row['Jugador']].tolist()
                            if idx_jug:
                                f_jug = idx_jug[0] + 2
                                camp_actual = str(df_j.at[idx_jug[0], 'Campeonato']).strip()
                                nuevo_camp = row['Campeonato_Deseado']
                                camp_final = f"{camp_actual}, {nuevo_camp}" if camp_actual else nuevo_camp
                                tabla_jugadores.update_cell(f_jug, 10, camp_final) 
                            st.cache_data.clear()
                            st.rerun()
                        if c3.button("❌ Rechazar", key=f"no_{idx_df}"):
                            tabla_solicitudes.update_cell(fila_excel, 3, "Rechazado")
                            st.cache_data.clear()
                            st.rerun()
        else: st.info("No hay solicitudes registradas en la base de datos.")

    # --- MENÚ: EL PADDOCK ---
    elif menu == "🏆 El Paddock":
        st.subheader(f"Clasificación Mundial - Campeonato: {st.session_state['campeonato_activo']}")
        df_q = fetch_data_quinielas()
        df_j = fetch_data_jugadores()
        
        if not df_q.empty and 'Campeonato' in df_q.columns:
            df_q.columns = [str(c).strip() for c in df_q.columns]
            df_q = df_q[df_q['Campeonato'].astype(str).str.strip() == st.session_state['campeonato_activo']]
            
            df_q['Puntos_Totales'] = pd.to_numeric(df_q.get('Puntos_Totales', 0), errors='coerce').fillna(0)
            res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index()
            
            if not df_j.empty:
                res = res.merge(df_j[['Nombre', 'Escuderia_Favorita']], left_on='Jugador', right_on='Nombre', how='left')
                res['🛡️'] = res['Escuderia_Favorita'].str.lower().str.strip().map(url_logos).fillna(url_logos["cadillac"])
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
                img_tag = f'<img src="{logo_url}" width="70">' if logo_url else ''
                html_table += '<tr style="border-bottom: 1px solid #444; background-color: transparent;">'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{img_tag}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row["Piloto"]}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle;">{row.get("Escudería", "")}</td>'
                html_table += f'<td style="text-align:center; padding: 10px; vertical-align: middle; font-weight: bold; font-size: 1.1rem;">{int(row["Puntos"])}</td>'
                html_table += '</tr>'
            html_table += '</tbody></table>'
            st.markdown(html_table, unsafe_allow_html=True)
        else: st.info("Aún no hay apuestas selladas en este campeonato.")

    # --- MENÚ: PADDOCK DETALLADO ---
    elif menu == "📊 Paddock Detallado":
        st.subheader(f"🔍 Análisis de Telemetría - Campeonato: {st.session_state['campeonato_activo']}")
        df_q = fetch_data_quinielas()
        df_j = fetch_data_jugadores()
        
        if not df_q.empty and 'Campeonato' in df_q.columns:
            df_q.columns = [str(c).strip() for c in df_q.columns]
            df_q = df_q[df_q['Campeonato'].astype(str).str.strip() == st.session_state['campeonato_activo']]

            op_v = st.selectbox("Ver:", ["🏆 Total"] + lista_carreras_oficial)
            if op_v == "🏆 Total":
                df_q['Puntos_Totales'] = pd.to_numeric(df_q.get('Puntos_Totales', 0), errors='coerce').fillna(0)
                res = df_q.groupby('Jugador')['Puntos_Totales'].sum().reset_index()
                if not df_j.empty:
                    res = res.merge(df_j[['Nombre', 'Escuderia_Favorita']], left_on='Jugador', right_on='Nombre', how='left')
                    res = res.rename(columns={'Jugador': 'Piloto', 'Escuderia_Favorita': 'Escudería', 'Puntos_Totales': 'Puntos'})
                    res = res[['Piloto', 'Escudería', 'Puntos']]
                else: res = res.rename(columns={'Jugador': 'Piloto', 'Puntos_Totales': 'Puntos'})
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
                cerrado_fari_detalle = False
                
                if not f_cal.empty:
                    if 'Es_Sprint' in f_cal.columns: es_sprint = str(f_cal.iloc[0]['Es_Sprint']).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'S']
                    
                    # --- CÁLCULO DE REGLA FARÍ PARA EL MODO ANTI-ESPIONAJE ---
                    fecha_q_str = f_cal.iloc[0].get('Fecha_Qualy', '')
                    ahora = datetime.utcnow() - timedelta(hours=6)
                    dt_q = pd.to_datetime(fecha_q_str, format="%H:%M %d-%m-%Y", errors='coerce')
                    if pd.notna(dt_q):
                        dias_para_jueves = dt_q.weekday() - 3 
                        jueves_limite = (dt_q - timedelta(days=dias_para_jueves)).replace(hour=23, minute=59, second=59)
                        if ahora > jueves_limite:
                            cerrado_fari_detalle = True

                if not df_f.empty:
                    def ac_n(n): return str(n).split()[-1] if (pd.notna(n) and " " in str(n)) else str(n)
                    todos_res = fetch_vals_resultados()
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
                    
                    if not cerrado_fari_detalle:
                        st.warning("🕵️‍♂️ **Modo Anti-Espionaje Activado:** Los pronósticos de los demás pilotos están ocultos. Se revelarán automáticamente el Jueves a las 23:59 hrs.")

                    html_det = '<table style="width:100%; text-align:center; border-collapse: collapse; font-family: sans-serif;">'
                    html_det += '<tr style="background-color: #2e2e3e; color: white;">'
                    for col in df_mostrar.columns:
                        titulo = "Piloto" if col == "Jugador" else col
                        html_det += f'<th style="text-align:center; padding: 10px; border-bottom: 2px solid #E10600; vertical-align: bottom;">{titulo}</th>'
                    html_det += '</tr>'

                    for _, row in df_mostrar.iterrows():
                        es_mi_fila = (row['Jugador'] == st.session_state['usuario_activo'])
                        html_det += '<tr style="border-bottom: 1px solid #444;">'
                        for col in df_mostrar.columns:
                            val = str(row[col]).strip() if pd.notna(row[col]) else ""
                            inner_html = val
                            
                            # MAGIA ANTI-ESPIONAJE
                            if col != 'Jugador' and "Pts" not in col:
                                if not cerrado_fari_detalle and not es_mi_fila and val not in ["", "nan", "None", "🔒 CERRADO"]:
                                    inner_html = '<span style="color: #888; font-style: italic;">🔒 Registrado</span>'
                                elif r_of:
                                    base = col.split('<br>')[0]
                                    if val not in ["", "nan", "None", "🔒 CERRADO"]:
                                        real = r_of.get(base, '')
                                        p1_real = r_of.get('P1', '')
                                        
                                        if base == 'Salado':
                                            if val == real and real != "": 
                                                inner_html = f'<span style="color: #FFD700; font-weight: bold; text-shadow: 1px 1px 2px #000;">{val}</span>'
                                            elif real != "" or p1_real != "": 
                                                inner_html = f'<span style="color: gray; font-weight: bold;">{val}</span>'
                                            else: 
                                                inner_html = val 
                                        else:
                                            if real != "":
                                                if val == real: 
                                                    inner_html = f'<span style="color: #00e676; font-weight: bold;">{val}</span>'
                                                elif base in ['P1','P2','P3', 'S1', 'S2', 'S3'] and val in [r_of.get(base[0]+'1'), r_of.get(base[0]+'2'), r_of.get(base[0]+'3')]: 
                                                    inner_html = f'<span style="color: #ffb300; font-weight: bold;">{val}</span>'
                                                elif base in ['Q1','Q2','Q3'] and val in [r_of.get('Q1'), r_of.get('Q2'), r_of.get('Q3')]: 
                                                    inner_html = f'<span style="color: #ffb300; font-weight: bold;">{val}</span>'
                                                else: 
                                                    inner_html = f'<span style="color: #ff5252; font-weight: bold;">{val}</span>'
                                            else:
                                                inner_html = val
                            elif "Pts" in col:
                                try:
                                    puntos_num = int(float(val))
                                except:
                                    puntos_num = 0
                                inner_html = f'<span style="font-weight: bold; font-size: 1.1rem;">{puntos_num}</span>'
                            html_det += f'<td style="padding: 10px; vertical-align: middle; text-align:center;">{inner_html}</td>'
                        html_det += '</tr>'
                    html_det += '</table>'
                    st.markdown(html_det, unsafe_allow_html=True)
        else: st.info("Aún no hay apuestas selladas en este campeonato para ver la telemetría.")

    # --- MENÚ: HACER APUESTA ---
    elif menu == "📝 Hacer Apuesta":
        gp_sel = st.selectbox("🌎 Selecciona GP:", lista_carreras_oficial, index=None, placeholder="Elige un Gran Premio...")
        if gp_sel:
            bq, bc, bs = True, True, True
            hora_q_txt, hora_c_txt, hora_s_txt = "", "", ""
            f = df_cal_global[df_cal_global['Carrera'] == gp_sel]
            es_sprint = False
            cerrado_fari = False
            
            if not f.empty:
                if 'Es_Sprint' in f.columns: es_sprint_val = str(f.iloc[0]['Es_Sprint']).strip().upper()
                else: es_sprint_val = 'NO'
                es_sprint = es_sprint_val in ['SI', 'SÍ', 'TRUE', '1', 'S']
                
                fecha_q_str = f.iloc[0].get('Fecha_Qualy', '')
                fecha_c_str = f.iloc[0].get('Fecha_Carrera', '')
                fecha_s_str = f.iloc[0].get('Fecha_Sprint', '') if 'Fecha_Sprint' in f.columns else ""
                
                if es_sprint: st.info(f"🕒 **Horarios Oficiales:** Qualy: {fecha_q_str} | Sprint: {fecha_s_str} | Carrera: {fecha_c_str} (🔥 SPRINT)")
                else: st.info(f"🕒 **Horarios Oficiales:** Qualy: {fecha_q_str} | Carrera: {fecha_c_str}")

                ahora = datetime.utcnow() - timedelta(hours=6)
                
                dt_q = pd.to_datetime(fecha_q_str, format="%H:%M %d-%m-%Y", errors='coerce')
                if pd.notna(dt_q):
                    dias_para_jueves = dt_q.weekday() - 3 
                    jueves_limite = (dt_q - timedelta(days=dias_para_jueves)).replace(hour=23, minute=59, second=59)
                    
                    if ahora > jueves_limite:
                        cerrado_fari = True
                        bq = bc = bs = True
                        st.error("🔒 PARQUE CERRADO (Regla Farí). Los pits se cerraron el Jueves a las 23:59 hrs CDMX. Ya no se aceptan ni se modifican apuestas.")

                if not cerrado_fari:
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
                        else: bs = bq
                    
            df_q = fetch_data_quinielas()
            if not df_q.empty: df_q.columns = [str(c).strip() for c in df_q.columns]
            
            if not df_q.empty and 'Campeonato' in df_q.columns:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel) & (df_q['Campeonato'].astype(str).str.strip() == st.session_state['campeonato_activo'])]
            else:
                filtro = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel)]
                
            ya_aposto, ap_p = not filtro.empty, filtro.iloc[-1].to_dict() if not filtro.empty else {}
            
            if ya_aposto: 
                if cerrado_fari: st.warning(f"🔒 Parque Cerrado. Este es tu pronóstico final e inamovible para **{st.session_state['campeonato_activo']}**.")
                else: st.info(f"📝 Ya tienes un pronóstico para **{st.session_state['campeonato_activo']}**. Puedes modificarlo las veces que quieras antes de que cierren los Pits.")

            def get_idx(campo): return pilotos.index(ap_p.get(campo)) if ya_aposto and ap_p.get(campo) in pilotos else None

            q_title = f" ({hora_q_txt} hrs CDMX)" if hora_q_txt else ""
            st.markdown(f"### ⏱️ Calificación{q_title}")
            q1_col, q2_col, q3_col = st.columns(3)
            with q1_col: q1 = st.selectbox("Q1:", pilotos, index=get_idx('Qualy_P1'), key=f"q1_{gp_sel}", placeholder="Elige...", disabled=bq or cerrado_fari)
            with q2_col: q2 = st.selectbox("Q2:", pilotos, index=get_idx('Qualy_P2'), key=f"q2_{gp_sel}", placeholder="Elige...", disabled=bq or cerrado_fari)
            with q3_col: q3 = st.selectbox("Q3:", pilotos, index=get_idx('Qualy_P3'), key=f"q3_{gp_sel}", placeholder="Elige...", disabled=bq or cerrado_fari)
            
            q_selections = [x for x in [q1, q2, q3] if x is not None]
            hay_error_q = len(q_selections) != len(set(q_selections))
            if hay_error_q: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en la Calificación.")

            st.write("---")
            s1, s2, s3 = None, None, None
            hay_error_s = False
            if es_sprint:
                s_title = f" ({hora_s_txt} hrs CDMX)" if hora_s_txt else ""
                st.markdown(f"### 🔥 Carrera Sprint{s_title}")
                s1_col, s2_col, s3_col = st.columns(3)
                with s1_col: s1 = st.selectbox("Sprint P1:", pilotos, index=get_idx('Sprint_P1'), key=f"s1_{gp_sel}", placeholder="Elige...", disabled=bs or cerrado_fari)
                with s2_col: s2 = st.selectbox("Sprint P2:", pilotos, index=get_idx('Sprint_P2'), key=f"s2_{gp_sel}", placeholder="Elige...", disabled=bs or cerrado_fari)
                with s3_col: s3 = st.selectbox("Sprint P3:", pilotos, index=get_idx('Sprint_P3'), key=f"s3_{gp_sel}", placeholder="Elige...", disabled=bs or cerrado_fari)
                
                s_selections = [x for x in [s1, s2, s3] if x is not None]
                hay_error_s = len(s_selections) != len(set(s_selections))
                if hay_error_s: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el Sprint.")
                st.write("---")
            
            c_title = f" ({hora_c_txt} hrs CDMX)" if hora_c_txt else ""
            st.markdown(f"### 🏁 Carrera Principal{c_title}")
            c1_col, c2_col, c3_col = st.columns(3)
            with c1_col: g1 = st.selectbox("P1:", pilotos, index=get_idx('Carrera_P1'), key=f"g1_{gp_sel}", placeholder="Elige...", disabled=bc or cerrado_fari)
            with c2_col: g2 = st.selectbox("P2:", pilotos, index=get_idx('Carrera_P2'), key=f"g2_{gp_sel}", placeholder="Elige...", disabled=bc or cerrado_fari)
            with c3_col: g3 = st.selectbox("P3:", pilotos, index=get_idx('Carrera_P3'), key=f"g3_{gp_sel}", placeholder="Elige...", disabled=bc or cerrado_fari)
            
            c_selections = [x for x in [g1, g2, g3] if x is not None]
            hay_error_c = len(c_selections) != len(set(c_selections))
            if hay_error_c: st.error("❌ ¡Bandera Negra! Tienes pilotos repetidos en el podio.")

            st.write("---")
            st.markdown("### 🎲 Bonos Especiales")
            b1_col, b2_col, b3_col = st.columns(3)
            with b1_col: vr = st.selectbox("🚀 VR:", pilotos, index=get_idx('Vuelta_Rapida'), key=f"v_{gp_sel}", placeholder="Elige...", disabled=bc or cerrado_fari)
            with b2_col: pdia = st.selectbox("🌟 PD:", pilotos, index=get_idx('Piloto_Del_Dia'), key=f"p_{gp_sel}", placeholder="Elige...", disabled=bc or cerrado_fari)
            with b3_col: ab = st.selectbox("💥 Abandono (Opcional):", pilotos, index=get_idx('Primer_Abandono'), key=f"a_{gp_sel}", placeholder="Ninguno", disabled=bc or cerrado_fari)

            st.write("---")
            
            aplicar_todos = st.checkbox("🏆 Aplicar esta misma quiniela a TODOS mis campeonatos", value=True, help="Si dejas esto marcado, se actualizará tu apuesta en todos tus campeonatos a la vez. Si lo quitas, solo se cambia en el que estás viendo.", disabled=cerrado_fari)

            btn_disabled = hay_error_q or hay_error_s or hay_error_c or cerrado_fari
            texto_btn = "🔄 Actualizar Apuesta" if ya_aposto else "🏎️ Sellar Apuesta"
            
            if st.button(texto_btn, disabled=btn_disabled):
                campos_obligatorios = [q1, q2, q3, g1, g2, g3, vr, pdia]
                if es_sprint: campos_obligatorios += [s1, s2, s3]
                
                if None in campos_obligatorios: 
                    st.warning("⚠️ ¡Pits incompletos! Faltan pronósticos por llenar.")
                else:
                    v_s1, v_s2, v_s3 = s1 if s1 else "", s2 if s2 else "", s3 if s3 else ""
                    
                    camps_a_guardar = [st.session_state['campeonato_activo']]
                    if aplicar_todos:
                        camps_a_guardar = [c for c in mis_camps if c != "Sin Campeonato"]
                        
                    celdas_a_actualizar = []
                    filas_a_agregar = []
                    
                    for c in camps_a_guardar:
                        if 'Campeonato' in df_q.columns:
                            filtro_c = df_q[(df_q['Jugador'] == st.session_state['usuario_activo']) & (df_q['Carrera'] == gp_sel) & (df_q['Campeonato'].astype(str).str.strip() == c)]
                        else:
                            filtro_c = pd.DataFrame()
                        
                        try:
                            val_pts = filtro_c.iloc[-1].get('Puntos_Totales', 0) if not filtro_c.empty else 0
                            pts_previos = int(val_pts.item()) if hasattr(val_pts, 'item') else int(val_pts)
                        except:
                            pts_previos = 0
                        
                        fila_guardar = [(datetime.utcnow()-timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), str(st.session_state['usuario_activo']), str(gp_sel), str(q1), str(q2), str(q3), str(v_s1), str(v_s2), str(v_s3), str(g1), str(g2), str(g3), str(vr), str(pdia), str(ab if ab else ""), pts_previos, str(c)]
                        
                        if not filtro_c.empty:
                            idx_pd = filtro_c.index[0]
                            row_excel = int(idx_pd.item()) + 2 if hasattr(idx_pd, 'item') else int(idx_pd) + 2
                            
                            for col_idx, val in enumerate(fila_guardar):
                                val_limpio = val.item() if hasattr(val, 'item') else val
                                celdas_a_actualizar.append(gspread.Cell(row=row_excel, col=int(col_idx)+1, value=val_limpio))
                        else:
                            filas_a_agregar.append(fila_guardar)
                            
                    if celdas_a_actualizar: tabla_quinielas.update_cells(celdas_a_actualizar)
                    for fila in filas_a_agregar: tabla_quinielas.append_row(fila)
                        
                    st.cache_data.clear()
                    
                    semaforo = st.empty()
                    luces = ["🔴 ⚪ ⚪ ⚪ ⚪", "🔴 🔴 ⚪ ⚪ ⚪", "🔴 🔴 🔴 ⚪ ⚪", "🔴 🔴 🔴 🔴 ⚪", "🔴 🔴 🔴 🔴 🔴"]
                    for luz in luces:
                        semaforo.markdown(f"<h1 style='text-align: center; letter-spacing: 15px;'>{luz}</h1>", unsafe_allow_html=True)
                        time.sleep(0.5) 
                        
                    time.sleep(0.8) 
                    semaforo.markdown("<h1 style='text-align: center; letter-spacing: 15px;'>🟢 🟢 🟢 🟢 🟢</h1><h3 style='text-align: center;'>🏎️💨 ¡Y ARRANCAN! Apuesta sellada.</h3>", unsafe_allow_html=True)
                    time.sleep(2) 
                    st.rerun()

    # --- MENÚ: CAMPEONATO REAL F1 ---
    elif menu == "🌍 Campeonato Real F1":
        st.header("🌍 Estado Actual del Campeonato Mundial F1 (Oficial)")
        st.write("Telemetría directa de la FIA con las posiciones reales y oficiales de la temporada actual.")

        @st.cache_data(ttl=3600) # Guarda los datos por 1 hora para no saturar la API
        def obtener_posiciones_reales():
            try:
                # API de Pilotos
                req_p = requests.get("https://api.jolpi.ca/ergast/f1/current/driverStandings.json").json()
                lista_p = req_p['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
                df_pilotos = pd.DataFrame([{
                    "Pos": int(d['position']),
                    "Piloto": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                    "Escudería": d['Constructors'][0]['name'],
                    "Puntos": float(d['points']),
                    "Victorias": int(d['wins'])
                } for d in lista_p])

                # API de Constructores
                req_c = requests.get("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json").json()
                lista_c = req_c['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
                df_escuderias = pd.DataFrame([{
                    "Pos": int(c['position']),
                    "Escudería": c['Constructor']['name'],
                    "Puntos": float(c['points']),
                    "Victorias": int(c['wins'])
                } for c in lista_c])
                
                return df_pilotos, df_escuderias
            except Exception as e:
                return None, None

        df_p_real, df_e_real = obtener_posiciones_reales()

        if df_p_real is not None:
            tab_pil, tab_esc = st.tabs(["🏎️ Campeonato de Pilotos", "🏗️ Campeonato de Constructores"])
            with tab_pil:
                st.dataframe(df_p_real, hide_index=True, use_container_width=True)
            with tab_esc:
                st.dataframe(df_e_real, hide_index=True, use_container_width=True)
        else:
            st.error("❌ Falla de comunicación con los servidores de la FIA. Intenta más tarde.")
    
    # --- REGLAMENTO Y ADMIN FIA ---
    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (La Regla Farí)")
        st.info("Para evitar espionaje durante las prácticas libres, **el Parque Cerrado se activa todos los JUEVES a las 23:59 hrs (Hora CDMX)** de la semana de carrera. Después de esa hora, nadie puede sellar ni modificar su quiniela. Sin excepciones.")
        st.markdown("### 🎯 ARTÍCULO 2: Sistema de Puntuación Detallado")
        st.success("""
        Para las secciones de **Calificación (Q1, Q2, Q3)**, **Carrera (P1, P2, P3)** y **Carreras Sprint (S1, S2, S3)** el puntaje se calcula así:
        * 🥇 **Posición Exacta:** **+3 Puntos**.
        * 🥈 **Acierto Desordenado:** **+1 Punto** (Top 3 de esa sesión pero en distinta posición).
        * 🚀 **Vuelta Rápida / Piloto del Día:** **+2 Puntos** por acierto exacto.
        """)
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("Esta apuesta es **OPCIONAL**. ✅ **Si Acertaste:** +5 Puntos directos. ❌ **Si Fallaste:** -2 Puntos.")
        st.markdown("### ⚖️ ARTÍCULO 4: El Director de Carrera es Dios")
        st.error("Los resultados son validados por el mismísimo **Sasian**. La decisión final es absoluta e inapelable.")

    # --- MANUAL DEL PILOTO Y FAQ ---
    elif menu == "📘 Manual del Piloto":
        st.header("🏎️ Manual del Piloto: SasianGP 2026")
        st.write("Bienvenido al Paddock. Esta aplicación está diseñada para medir tu conocimiento (y tu suerte) en la Fórmula 1. Aquí te explicamos cómo funcionan los tableros de tu monoplaza.")
        
        st.markdown("---")
        st.subheader("🎛️ Instrucciones Rápidas por Módulo")
        
        with st.expander("1. 📝 Hacer Apuesta (Tus Pits)"):
            st.markdown("""
            Aquí es donde configuras tu auto para el fin de semana.
            * **Selecciona el GP:** Elige la carrera en turno.
            * **Llena tu pronóstico:** Selecciona a los pilotos para la Calificación (Q1, Q2, Q3), la Carrera (P1, P2, P3), y si es fin de semana especial, la Carrera Sprint.
            * **Bonos:** Acierta la Vuelta Rápida (VR) y el Piloto del Día (PD).
            * **El Riesgo (Abandono):** Puedes apostar quién será el primero en chocar o romper el motor. Es opcional, pero da muchos puntos (o te los quita).
            * **Sellar Apuesta:** Dale clic al botón y espera a que el semáforo cambie a verde para confirmar que tu telemetría se guardó.
            """)
        
        with st.expander("2. 🏆 El Paddock"):
            st.write("La tabla de posiciones general. Aquí verás el Campeonato Mundial en tiempo real para la liga en la que estás activo. Revisa quién va liderando y quién se está quedando rezagado.")
            
        with st.expander("3. 📊 Paddock Detallado (Telemetría)"):
            st.markdown("""
            El escáner a fondo de cada carrera. 
            * Selecciona un Gran Premio específico para ver exactamente qué piloto apostó cada quién.
            * **🕵️‍♂️ Modo Anti-Espionaje:** Para evitar copias, los pronósticos de los demás pilotos se mantendrán ocultos como *'🔒 Registrado'* y se revelarán automáticamente al cerrarse los Pits (Jueves 23:59 hrs).
            * **Código de colores:** Sabrás al instante por qué ganaste o perdiste puntos. Verde (+3 acierto exacto), Amarillo (+1 acierto desordenado), Rojo (0 fallaste), Dorado (+5 acierto Salado) y Gris (-2 fallaste el Salado).
            """)
            
        with st.expander("4. 📖 Reglamento Oficial"):
            st.write("Las reglas inquebrantables de la FIA (dictadas por el Comisario Sasian). Échale un ojo para entender a detalle cuántos puntos da cada sección y cómo funciona el bloqueo de apuestas.")
            
        with st.expander("5. 🛡️ Administrar mis Campeonatos (Solo Creadores)"):
            st.write("Si tú creaste un campeonato privado, tú eres el cadenero. Aquí te aparecerán las solicitudes de tus amigos que quieren entrar a tu liga. Tienes el poder absoluto de **Aprobarlos** o **Rechazarlos**.")

        st.markdown("---")
        st.subheader("❓ Preguntas Frecuentes (FAQ)")
        
        st.markdown("**1. ¿Hasta qué día y hora puedo meter o cambiar mi pronóstico?**")
        st.info("Por la sagrada **'Regla Farí'**, los Pits se cierran automáticamente todos los **JUEVES a las 23:59 hrs (Hora de la CDMX)** de la semana de carrera. Después de esa hora, entra el Parque Cerrado y el sistema bloquea cualquier intento de apuesta o modificación.")
        
        st.markdown("**2. Me salí a contestar un mensaje y al regresar a la app me sacó. ¿Por qué se cierra mi sesión?**")
        st.info("""
        La app usa un 'Llavero Virtual' (Cookies) para recordar que estás adentro. Sin embargo, los navegadores de los celulares bloquean estas llaves por defecto al considerarlas externas. Para que tu sesión sea infinita, configura tu teléfono así:
        
        * 🍎 **Si usas iPhone (Safari):** Ve a los **Ajustes** de tu iPhone > **Aplicaciones** > **Safari**. Baja hasta la sección de Privacidad y Seguridad y **APAGA** el interruptor que dice **'Prevenir rastreo entre sitios'**.
        
        * 🤖 **Si usas Android (Chrome):** Abre tu navegador Chrome, toca los 3 puntos (arriba a la derecha) > **Configuración** > **Configuración de sitios** > **Cookies de terceros** y selecciona **'Permitir cookies de terceros'**.
        
        *(Nota de Dirección de Carrera: Después de hacer este ajuste, inicia sesión una vez más en la app para que el sistema te entregue tu llave definitiva).*
        """)
        st.markdown("**3. Olvidé mi contraseña secreta, ¿qué hago?**")
        st.success("Cierra sesión (o abre la app en modo incógnito). En la pantalla de acceso busca la pestaña **'🆘 Olvidé mi Clave'**. Pon el alias con el que corres, dale al botón, y Dirección de Carrera te mandará tu contraseña al correo electrónico con el que te registraste.")
        
        st.markdown("**4. ¿Puedo estar en varios campeonatos a la vez?**")
        st.success("¡Sí! En tu menú lateral tienes un botón de **'➕ Unirme a otro'**. Puedes mandar solicitud para unirte a ligas de otros amigos. Cuando vayas a hacer tu apuesta, hay una casilla que te permite aplicar ese mismo pronóstico a todas tus ligas al mismo tiempo.")
        
        st.markdown("**5. Me acabo de registrar pero me sale un error de 'Sala de Espera'.**")
        st.warning("Es normal. Cuando firmas contrato para unirte a una liga ya existente, tu acceso se queda en 'Pendiente'. Tienes que avisarle al creador de ese campeonato para que entre a su módulo de Administración y te acepte en el Paddock.")
        
        st.markdown("**6. ¿Qué es la apuesta de 'Abandono' o 'Salado'?**")
        st.warning("Es de alto riesgo. Tratas de adivinar quién será el primer piloto en abandonar la carrera.\n* ✅ Si aciertas, ganas **+5 puntos** directos.\n* ❌ Si fallas, te penalizan con **-2 puntos**.\n* *Tip:* Puedes dejarlo en 'Ninguno' si no quieres arriesgarte.")
        
        st.markdown("**7. La app me sacó una 'Bandera Negra' al intentar guardar mi apuesta, ¿por qué?**")
        st.error("Seguramente pusiste al mismo piloto dos veces en la misma sección (ej. a Verstappen en P1 y también en P2). Revisa que no tengas nombres repetidos en tus podios; la app no te dejará avanzar hasta que lo corrijas.")

        st.markdown("**8. ¿Por qué veo candados (🔒 Registrado) en lugar de los pronósticos de los demás?**")
        st.info("Es el **Modo Anti-Espionaje**. Para evitar que se copien estrategias, solo puedes ver tu propio pronóstico antes de la carrera. En el instante en que se cierra la ventana de apuestas (Jueves 23:59 hrs), el sistema quita la lona y revela las apuestas de toda la parrilla automáticamente.")

    elif menu == "👑 Admin FIA":
        st.header("📢 Pizarra de Dirección de Carrera")
        with st.expander("Modificar Mensaje Global"):
            with st.form("form_mensaje"):
                nuevo_msg = st.text_area("Texto del mensaje (deja en blanco para borrarlo):")
                tipo_msg = st.selectbox("Tipo de Mensaje:", ["Informativo", "Crítico", "Alerta", "Éxito"])
                
                if st.form_submit_button("📡 Transmitir a todos los pilotos"):
                    tabla_mensajes.update_cell(2, 1, nuevo_msg)
                    tabla_mensajes.update_cell(2, 2, tipo_msg)
                    st.cache_data.clear()
                    st.success("✅ Mensaje transmitido a toda la parrilla.")
                    st.rerun()
        st.markdown("---")
        
        sel_car = st.selectbox("Gran Premio a Dictaminar:", lista_carreras_oficial)
        f_cal = df_cal_global[df_cal_global['Carrera'] == sel_car]
        es_sprint = False
        if not f_cal.empty:
            if 'Es_Sprint' in f_cal.columns: es_sprint = str(f_cal.iloc[0]['Es_Sprint']).strip().upper() in ['SI', 'SÍ', 'TRUE', '1', 'S']
        
        todos_resultados = fetch_vals_resultados()
        res_previos = {}
        for fila in reversed(todos_resultados):
            if len(fila) >= 13 and fila[0] == sel_car:
                res_previos = {'rq1': fila[1], 'rq2': fila[2], 'rq3': fila[3], 'rs1': fila[4], 'rs2': fila[5], 'rs3': fila[6], 'rg1': fila[7], 'rg2': fila[8], 'rg3': fila[9], 'rvr': fila[10], 'rpd': fila[11], 'rab': fila[12]}
                break

        if res_previos: st.info("💡 Ya hay resultados oficiales guardados para esta carrera.")

        def get_idx_res(llave, d_v=None):
            if res_previos and llave in res_previos and res_previos[llave] in pilotos: return pilotos.index(res_previos[llave])
            if d_v in pilotos: return pilotos.index(d_v)
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
                v_rq1 = rq1 if rq1 else ""
                v_rq2 = rq2 if rq2 else ""
                v_rq3 = rq3 if rq3 else ""
                v_rs1 = rs1 if rs1 else ""
                v_rs2 = rs2 if rs2 else ""
                v_rs3 = rs3 if rs3 else ""
                v_rg1 = rg1 if rg1 else ""
                v_rg2 = rg2 if rg2 else ""
                v_rg3 = rg3 if rg3 else ""
                v_rvr = rvr if rvr else ""
                v_rpd = rpd if rpd else ""
                v_abr = abr if abr else ""

                tabla_resultados.append_row([sel_car, v_rq1, v_rq2, v_rq3, v_rs1, v_rs2, v_rs3, v_rg1, v_rg2, v_rg3, v_rvr, v_rpd, v_abr])
                st.cache_data.clear()
                
                df_q = fetch_data_quinielas()
                headers_q = [str(h).strip() for h in df_q.columns.tolist()]
                
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
                            
                            # 🔧 EL BLINDAJE PERFECTO DEL SALADO
                            v_ab_jugador = str(row.get('Primer_Abandono','')).strip()
                            if v_ab_jugador and v_ab_jugador != "🔒 CERRADO" and v_ab_jugador.lower() != "ninguno":
                                if v_abr: 
                                    if v_ab_jugador == v_abr: p += 5
                                    else: p -= 2
                                elif v_rg1: 
                                    p -= 2
                                
                            celdas.append(gspread.Cell(row=i+2, col=col_pts_idx, value=p))
                    
                    if celdas: 
                        tabla_quinielas.update_cells(celdas)
                        st.cache_data.clear()
                    st.success("🏆 ¡Puntos repartidos a todos los campeonatos al milímetro!")
                else:
                    st.error("Error: No encontré la columna 'Puntos_Totales' en Quinielas.")
