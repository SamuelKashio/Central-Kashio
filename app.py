#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUPERVISIÓN: Login/Logout y Sesiones de Agentes
Código Python limpio - Sin markdown, listo para copiar a app.py
"""

# ── SUPERVISIÓN: Login/Logout y Sesiones ────────────────────────────────────
def detectar_eventos_login_logout(df_sal):
    """Detecta llamadas *34 (login) y *33 (logout) como eventos especiales"""
    if df_sal is None or df_sal.empty:
        return pd.DataFrame()
    
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
            login_time = evt["detect_time"]
            login_idx = idx
        elif "*33" in str(evt.get("numero_cliente", "")) and login_time:
            logout_time = evt["detect_time"]
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
                "logout": logout_time,
                "duracion_minutos": duracion_minutos,
                "llamadas_totales": llamadas_count,
                "llamadas_atendidas": llamadas_atendidas,
                "llamadas_no_atendidas": llamadas_count - llamadas_atendidas,
                "duracion_promedio_llamada": 0 if llamadas_count == 0 else duracion_segundos / llamadas_count
            })
            
            login_time = None
            login_idx = None
    
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
            "logout": None,
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
        return {"estado": "Desconocido", "desde": None, "duracion": "—"}
    
    eventos = df_sal[
        (df_sal["agente_id"] == agent_id) &
        (df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
    ].copy().sort_values("detect_time", ascending=False)
    
    if eventos.empty:
        return {"estado": "Desconocido", "desde": None, "duracion": "—"}
    
    ultimo_evento = eventos.iloc[0]
    es_login = "*34" in str(ultimo_evento.get("numero_cliente", ""))
    
    if es_login:
        duracion_min = int((now_lima - ultimo_evento["detect_time"]).total_seconds() / 60)
        horas = duracion_min // 60
        minutos = duracion_min % 60
        
        return {
            "estado": "Online",
            "desde": ultimo_evento["detect_time"],
            "duracion": f"{horas}h {minutos}m"
        }
    else:
        return {
            "estado": "Offline",
            "desde": ultimo_evento["detect_time"],
            "duracion": "—"
        }


def calcular_metricas_supervisor(df_sal, df_ent, agent_id):
    """Calcula métricas completas para supervisión"""
    if df_sal is None or df_sal.empty:
        return {}
    
    hoy = now_lima.date()
    sesiones = calcular_sesiones_agente(df_sal, agent_id)
    sesiones_hoy = [s for s in sesiones if s["fecha"] == hoy]
    
    llamadas_hoy = df_sal[
        (df_sal["agente_id"] == agent_id) &
        (df_sal["detect_time"].dt.date == hoy) &
        (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))
    ]
    
    llamadas_atendidas = (llamadas_hoy["atendida"] == True).sum()
    llamadas_no_atendidas = len(llamadas_hoy) - llamadas_atendidas
    
    duracion_promedio = int(llamadas_hoy["duracion"].mean()) if len(llamadas_hoy) > 0 else 0
    
    tiempo_conectado = sum([s["duracion_minutos"] for s in sesiones_hoy])
    
    horas_conectado = tiempo_conectado / 60
    productividad = len(llamadas_hoy) / horas_conectado if horas_conectado > 0 else 0
    
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
                    if gap > 5:
                        pausas.append(int(gap))
    
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
