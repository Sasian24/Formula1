    elif menu == "📖 Reglamento Oficial":
        st.header("📜 REGLAMENTO DEPORTIVO SASIANGP 2026")
        st.write("Bienvenidos a la máxima categoría. Aquí venimos a apostar el honor, no a hacer amigos. Lean las reglas a detalle para que luego no anden llorando por los rincones exigiendo puntos que no se ganaron.")
        st.markdown("---")
        st.markdown("### ⏱️ ARTÍCULO 1: El Reloj No Perdona (Cierre de Pits)")
        st.info("El sistema cuenta con un **Reloj Suizo** automático en formato de 24 hrs. \n* **Calificación (Qualy):** Se bloquea **EXACTAMENTE 1 HORA ANTES** de que los autos salgan a la pista.\n* **Carrera:** Se bloquea **EXACTAMENTE 1 HORA ANTES** del semáforo en verde.\n* **Excepciones:** NINGUNA. Si entras a la app 59 minutos antes, las cajitas estarán en gris y te vas con 0 puntos. Ni mandándole WhatsApp a Sasian se abre.")
        st.markdown("### 🎯 ARTÍCULO 2: El Podio (Precisión Absoluta)")
        st.success("Aquí no hay premios de consolación por 'casi' atinarle. O le das a la posición exacta o tienes cero.\n* 🥇 **Ganador (P1):** +3 Puntos.\n* 🥈 **Segundo (P2):** +3 Puntos.\n* 🥉 **Tercer (P3):** +3 Puntos.\n* ⏱️ **Pole Position (Qualy P1):** +3 Puntos.\n* 🚀 **Vuelta Rápida:** +2 Puntos si adivinas quién hace el giro más rápido el domingo.")
        st.markdown("### ☠️ ARTÍCULO 3: El Bono 'Salado' (Riesgo Extremo)")
        st.warning("Esta apuesta es **OPCIONAL**.\n* ✅ **Si Acertaste:** Si tu piloto es el primero en abandonar, eres un genio del mal y te llevas **+5 Puntos** directos.\n* ❌ **Si Fallaste:** Si sobrevive o alguien más abandona antes, te castigamos con **-2 Puntos**.\n* 🛡️ **Tip:** Dejar el espacio en blanco es totalmente válido y te salva de perder puntos.")
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
