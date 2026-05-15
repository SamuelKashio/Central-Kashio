# 🎯 IMPLEMENTACIÓN COMPLETA: Sistema de Supervisión de Agentes

## 📊 RESUMEN DE LA SOLUCIÓN

Este sistema detecta las llamadas salientes `*34` (login) y `*33` (logout) como eventos especiales y calcula:

✅ **Conexión/Desconexión:** Hora login, hora logout, duración sesión  
✅ **Pausas:** Detecta períodos sin llamadas entre logins  
✅ **Llamadas:** Cuenta llamadas durante sesión  
✅ **Descansos:** Tiempo entre logout y siguiente login  
✅ **Productividad:** Llamadas/hora, duración promedio  

---

## 📋 PASO 1: Agregar Funciones de Supervisión

Agrega estas funciones **después de `calcular_cumplimiento()`** (alrededor de línea 360):

```python
# ── SUPERVISIÓN: Login/Logout y Sesiones ────────────────────────────────────
def detectar_eventos_login_logout(df_sal):
    """Detecta llamadas *34 (login) y *33 (logout) como eventos especiales"""
    if df_sal is None or df_sal.empty:
        return pd.DataFrame()
    
    # Identificar logins (*34) y logouts (*33)
    eventos = df_sal[
        df_sal["numero_cliente"].astype(str).isin(["*34", "*33"])
    ].copy()
    
    if eventos.empty:
        return pd.DataFrame()
    
    eventos["tipo_evento"] = eventos["numero_cliente"].map({"*34": "LOGIN", "*33": "LOGOUT"})
    eventos = eventos.sort_values("detect_time", ascending=False)
    
    return eventos[["detect_time", "agente", "agente_id", "numero_cliente", "tipo_evento", "duracion"]]

def calcular_sesiones_agente(df_sal, agent_id):
    """Calcula sesiones de login/logout para un agente específico"""
    if df_sal is None or df_sal.empty:
        return []
    
    # Obtener eventos del agente
    eventos = df_sal[
        (df_sal["agente_id"] == agent_id) & 
        (df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
    ].copy().sort_values("detect_time")
    
    if eventos.empty:
        return []
    
    sesiones = []
    login_time = None
    login_idx = None
    
    for idx, evt in eventos.iterrows():
        if "*34" in str(evt.get("numero_cliente", "")):
            # Es un LOGIN
            login_time = evt["detect_time"]
            login_idx = idx
        elif "*33" in str(evt.get("numero_cliente", "")) and login_time:
            # Es un LOGOUT
            logout_time = evt["detect_time"]
            duracion_segundos = (logout_time - login_time).total_seconds()
            duracion_minutos = int(duracion_segundos / 60)
            
            # Contar llamadas durante la sesión
            llamadas_sesion = df_sal[
                (df_sal["agente_id"] == agent_id) &
                (df_sal["detect_time"] >= login_time) &
                (df_sal["detect_time"] <= logout_time) &
                (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
            ]
            
            llamadas_count = len(llamadas_sesion)
            llamadas_atendidas = (llamadas_sesion["atendida"] == True).sum()
            
            sesiones.append({
                "fecha": login_time.date(),
                "login": login_time,
                "logout": logout_time,
                "duracion_minutos": duracion_minutos,
                "llamadas_totales": llamadas_count,
                "llamadas_atendidas": llamadas_atendidas,
                "llamadas_no_atendidas": llamadas_count - llamadas_atendidas,
                "duracion_promedio_llamada": 0 if llamadas_count == 0 else duracion_segundos / llamadas_count
            })
            
            login_time = None
            login_idx = None
    
    # Si sigue logueado (sin logout), crear sesión abierta
    if login_time:
        logout_time = now_lima
        duracion_segundos = (logout_time - login_time).total_seconds()
        duracion_minutos = int(duracion_segundos / 60)
        
        llamadas_sesion = df_sal[
            (df_sal["agente_id"] == agent_id) &
            (df_sal["detect_time"] >= login_time) &
            (df_sal["detect_time"] <= logout_time) &
            (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
        ]
        
        llamadas_count = len(llamadas_sesion)
        llamadas_atendidas = (llamadas_sesion["atendida"] == True).sum()
        
        sesiones.append({
            "fecha": login_time.date(),
            "login": login_time,
            "logout": None,  # Sesión abierta
            "duracion_minutos": duracion_minutos,
            "llamadas_totales": llamadas_count,
            "llamadas_atendidas": llamadas_atendidas,
            "llamadas_no_atendidas": llamadas_count - llamadas_atendidas,
            "duracion_promedio_llamada": 0 if llamadas_count == 0 else duracion_segundos / llamadas_count,
            "activa": True
        })
    
    return sesiones

def obtener_estado_actual_agente(df_sal, agent_id):
    """Obtiene estado actual de un agente (online/offline)"""
    if df_sal is None or df_sal.empty:
        return {"estado": "⚪ Desconocido", "desde": None, "duracion": "—"}
    
    # Obtener últimos eventos del agente
    eventos = df_sal[
        (df_sal["agente_id"] == agent_id) &
        (df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
    ].copy().sort_values("detect_time", ascending=False)
    
    if eventos.empty:
        return {"estado": "⚪ Desconocido", "desde": None, "duracion": "—"}
    
    ultimo_evento = eventos.iloc[0]
    es_login = "*34" in str(ultimo_evento.get("numero_cliente", ""))
    
    if es_login:
        duracion_min = int((now_lima - ultimo_evento["detect_time"]).total_seconds() / 60)
        horas = duracion_min // 60
        minutos = duracion_min % 60
        
        return {
            "estado": "🟢 Online",
            "desde": ultimo_evento["detect_time"],
            "duracion": f"{horas}h {minutos}m"
        }
    else:
        return {
            "estado": "🔴 Offline",
            "desde": ultimo_evento["detect_time"],
            "duracion": "—"
        }

def calcular_metricas_supervisor(df_sal, df_ent, agent_id):
    """Calcula métricas completas para supervisión"""
    if df_sal is None or df_sal.empty:
        return {}
    
    # Obtener sesiones del agente hoy
    hoy = now_lima.date()
    sesiones = calcular_sesiones_agente(df_sal, agent_id)
    sesiones_hoy = [s for s in sesiones if s["fecha"] == hoy]
    
    # Llamadas totales del agente hoy
    llamadas_hoy = df_sal[
        (df_sal["agente_id"] == agent_id) &
        (df_sal["detect_time"].dt.date == hoy) &
        (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
    ]
    
    # Llamadas atendidas
    llamadas_atendidas = (llamadas_hoy["atendida"] == True).sum()
    llamadas_no_atendidas = len(llamadas_hoy) - llamadas_atendidas
    
    # Duración promedio de llamadas
    duracion_promedio = int(llamadas_hoy["duracion"].mean()) if len(llamadas_hoy) > 0 else 0
    
    # Tiempo total conectado
    tiempo_conectado = sum([s["duracion_minutos"] for s in sesiones_hoy])
    
    # Productividad (llamadas por hora)
    horas_conectado = tiempo_conectado / 60
    productividad = len(llamadas_hoy) / horas_conectado if horas_conectado > 0 else 0
    
    # Pausas (detectar periodos sin llamadas)
    pausas = []
    if len(sesiones_hoy) > 0:
        for sesion in sesiones_hoy:
            llamadas_sesion = df_sal[
                (df_sal["agente_id"] == agent_id) &
                (df_sal["detect_time"] >= sesion["login"]) &
                (df_sal["detect_time"] <= (sesion["logout"] or now_lima))
            ].copy().sort_values("detect_time")
            
            if len(llamadas_sesion) > 1:
                for i in range(len(llamadas_sesion) - 1):
                    gap = (llamadas_sesion.iloc[i+1]["detect_time"] - llamadas_sesion.iloc[i]["detect_time"]).total_seconds() / 60
                    if gap > 5:  # Pausa > 5 minutos
                        pausas.append(int(gap))
    
    # Descansos (tiempo entre logout y siguiente login)
    descansos = []
    if len(sesiones_hoy) > 1:
        for i in range(len(sesiones_hoy) - 1):
            if sesiones_hoy[i]["logout"] and sesiones_hoy[i+1]["login"]:
                descanso = (sesiones_hoy[i+1]["login"] - sesiones_hoy[i]["logout"]).total_seconds() / 60
                descansos.append(int(descanso))
    
    return {
        "llamadas_totales": len(llamadas_hoy),
        "llamadas_atendidas": llamadas_atendidas,
        "llamadas_no_atendidas": llamadas_no_atendidas,
        "duracion_promedio_llamada": duracion_promedio,
        "tiempo_conectado_minutos": tiempo_conectado,
        "productividad_llamadas_por_hora": round(productividad, 2),
        "pausas": pausas,
        "descansos": descansos,
        "sesiones_hoy": len(sesiones_hoy)
    }
```

---

## 📋 PASO 2: Agregar Nueva Pestaña

Busca esta línea (alrededor de línea 600):

```python
tab_overview, tab_ent, tab_sal, tab_ag, tab_turnos, tab_seg, tab_cl, tab_raw_t = st.tabs([...])
```

Reemplázala con:

```python
tab_overview, tab_ent, tab_sal, tab_ag, tab_turnos, tab_seg, tab_cl, tab_sup, tab_raw_t = st.tabs([
    "📊 Overview", "📈 Entrantes", "📉 Salientes", "👥 Agentes", "🕐 Turnos", 
    "📋 Seguimiento", "📞 Clientes", "👤 Supervisión", "📋 Raw"
])
```

---

## 📋 PASO 3: Agregar Contenido de la Pestaña Supervisión

Agrega esto **antes de `with tab_raw_t:`** (al final, alrededor de línea 1015):

```python
with tab_sup:
    st.markdown("#### 👤 Supervisión de Agentes")
    
    # Obtener eventos de login/logout
    eventos = detectar_eventos_login_logout(df_sal)
    
    # ─── TAB SUPERVISOR ───
    sup_tab1, sup_tab2, sup_tab3 = st.tabs(["📊 Estado Actual", "📈 Métricas Hoy", "📋 Historial"])
    
    with sup_tab1:
        st.markdown("**Estado Actual de Conexión**")
        
        agentes_cols = st.columns(3)
        col_idx = 0
        
        for aid, info in sorted(st.session_state.cfg_agentes.items()):
            if info.get("es_central"): continue
            
            col = agentes_cols[col_idx % 3]
            col_idx += 1
            
            estado_info = obtener_estado_actual_agente(df_sal, aid)
            estado_txt = estado_info["estado"]
            duracion_txt = estado_info["duracion"]
            desde_txt = estado_info["desde"].strftime("%H:%M") if estado_info["desde"] else "—"
            
            # Color según estado
            if "🟢" in estado_txt:
                color_fondo = c["green_border"]
                color_borde = c["green"]
            elif "🔴" in estado_txt:
                color_fondo = c["red_border"]
                color_borde = c["red"]
            else:
                color_fondo = c["border"]
                color_borde = c["muted"]
            
            with col:
                st.markdown(f"""
                <div style='background:{c["card"]};border:2px solid {color_fondo};border-radius:12px;padding:16px;text-align:center'>
                    <div style='font-size:24px;margin-bottom:8px'>{estado_txt.split()[0]}</div>
                    <div style='color:{c["text"]};font-weight:600;margin-bottom:8px'>{info["nombre"]}</div>
                    <div style='color:{c["muted"]};font-size:12px'>
                        <div>Desde: {desde_txt}</div>
                        <div>Duración: {duracion_txt}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with sup_tab2:
        st.markdown("**Métricas de Hoy por Agente**")
        
        metricas_rows = []
        for aid, info in st.session_state.cfg_agentes.items():
            if info.get("es_central"): continue
            
            metr = calcular_metricas_supervisor(df_sal, df_ent, aid)
            
            if not metr:
                continue
            
            estado_info = obtener_estado_actual_agente(df_sal, aid)
            estado_icon = estado_info["estado"].split()[0]
            
            metricas_rows.append({
                "Estado": estado_icon,
                "Agente": info["nombre"],
                "Llamadas": metr.get("llamadas_totales", 0),
                "Atendidas": metr.get("llamadas_atendidas", 0),
                "Dur.Prom": f"{metr.get('duracion_promedio_llamada', 0)}s",
                "Conectado": f"{metr.get('tiempo_conectado_minutos', 0)}m",
                "Productividad": f"{metr.get('productividad_llamadas_por_hora', 0):.1f}c/h",
                "Pausas": len(metr.get("pausas", [])),
                "Descansos": len(metr.get("descansos", []))
            })
        
        if metricas_rows:
            df_metricas = pd.DataFrame(metricas_rows)
            st.dataframe(df_metricas, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("Sin datos de supervisión disponibles")
    
    with sup_tab3:
        st.markdown("**Historial de Login/Logout - Hoy**")
        
        if not eventos.empty:
            eventos_hoy = eventos[
                eventos["detect_time"].dt.date == now_lima.date()
            ].copy()
            
            if not eventos_hoy.empty:
                hist_rows = []
                for _, evt in eventos_hoy.iterrows():
                    hist_rows.append({
                        "Hora": evt["detect_time"].strftime("%H:%M:%S"),
                        "Agente": evt["agente"],
                        "Evento": evt["tipo_evento"],
                        "Código": evt["numero_cliente"]
                    })
                
                df_hist = pd.DataFrame(hist_rows)
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                
                # Descargar historial
                st.download_button(
                    "⬇ Exportar Historial",
                    data=df_hist.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"supervision_{now_lima.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Sin eventos de login/logout registrados hoy")
        else:
            st.info("Sin datos de login/logout disponibles")
```

---

## ✅ RESUMEN DE CAMBIOS

| Qué | Dónde | Línea Aprox |
|-----|-------|-----------|
| Agregar funciones | Después de `calcular_cumplimiento()` | ~365 |
| Modificar tabs | Sección de `st.tabs()` | ~600 |
| Agregar contenido pestaña | Antes de `with tab_raw_t:` | ~1015 |

---

## 🎯 Métricas que Calcula

### Por Sesión de Agente:
- ✅ Hora login / Hora logout
- ✅ Duración total sesión
- ✅ Llamadas durante sesión
- ✅ Llamadas atendidas vs no atendidas

### Por Día:
- ✅ Llamadas totales
- ✅ Duración promedio por llamada
- ✅ Tiempo total conectado
- ✅ Productividad (llamadas/hora)
- ✅ Pausas detectadas
- ✅ Descansos entre sesiones

### Estado Actual:
- ✅ Online / Offline
- ✅ Hora desde la que está así
- ✅ Duración de sesión actual

---

## 🚀 Cómo Instalar

1. **Abre tu `app.py` en GitHub**
2. **Copia el CÓDIGO DE PASO 1** (funciones)
3. **Busca `calcular_cumplimiento()`** y pégalo después
4. **Copia CÓDIGO DE PASO 2** (modificar tabs)
5. **Copia CÓDIGO DE PASO 3** (pestaña supervisión)
6. **Commit a GitHub**
7. **Espera redeploy (3-5 min)**

---

## 📍 Ubicación Exacta en app.py

```
Línea 1-50:       Imports y configuración
Línea 50-400:     Funciones auxiliares
→ AQUÍ AGREGAR FUNCIONES DE SUPERVISIÓN (Paso 1)
Línea 400-600:    Carga de datos y clasificación
→ AQUÍ MODIFICAR TABS (Paso 2)
Línea 600-1000:   Tabs y visualizaciones
→ AQUÍ AGREGAR PESTAÑA SUPERVISIÓN (Paso 3)
Línea 1000+:      Tab Raw Data
```

---

## ⚠️ Notas Importantes

- **Los códigos `*34` y `*33` deben estar en `numero_cliente`** (campo `dnis` después de procesamiento)
- **Se detectan en `df_sal` (llamadas salientes)**
- **Las métricas se recalculan en cada carga de datos**
- **Todo se almacena en memoria** (persiste en sesión actual)

---

## 🎉 Resultado Final

Tendrás una nueva pestaña "👤 Supervisión" con 3 sub-tabs:

1. **📊 Estado Actual** → Cards con estado de cada agente
2. **📈 Métricas Hoy** → Tabla con productividad, llamadas, etc.
3. **📋 Historial** → Todos los logins/logouts del día

¿Necesitas ayuda para implementarlo? 💼
