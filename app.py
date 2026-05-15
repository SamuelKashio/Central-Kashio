import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time, json, os

TZ = ZoneInfo("America/Lima")
def now_lima(): return datetime.now(TZ).replace(tzinfo=None)

try:
    _U = st.secrets["CMW_USER"]
    _P = st.secrets["CMW_PASS"]
except Exception:
    st.error("Configura CMW_USER y CMW_PASS en .streamlit/secrets.toml"); st.stop()

# ── Defaults
DEFAULT_AGENTES = {
    "8668106":{"nombre":"Central Virtual","activo":True, "es_central":True},
    "8668109":{"nombre":"Alonso Loyola",  "activo":True, "es_central":False},
    "8668110":{"nombre":"Jose Luis Cahuana","activo":True,"es_central":False},
    "8668112":{"nombre":"Daniel Huayta",  "activo":True, "es_central":False},
    "8668111":{"nombre":"Deivy Chavez",   "activo":True, "es_central":False},
    "8668114":{"nombre":"Joe Villanueva", "activo":True, "es_central":False},
    "8672537":{"nombre":"Victor Figueroa","activo":True, "es_central":False},
}
DEFAULT_TURNOS = [
    {"dias":[0,1,2,3,4],"h_ini": 6,"h_fin":14,"agente":"Alonso Loyola",    "activo":True},
    {"dias":[0,1,2,3,4],"h_ini":14,"h_fin":22,"agente":"Jose Luis Cahuana","activo":True},
    {"dias":[0,1,2,3,4],"h_ini":22,"h_fin":30,"agente":"Deivy Chavez",     "activo":True},
    {"dias":[5,6],      "h_ini": 6,"h_fin":14,"agente":"Daniel Huayta",    "activo":True},
    {"dias":[5,6],      "h_ini":14,"h_fin":22,"agente":"Luz Goicochea",    "activo":True},
    {"dias":[5,6],      "h_ini":22,"h_fin":30,"agente":"Joe Villanueva",   "activo":True},
]
DEFAULT_NUMS_EXCLUIDOS = ["51902871550"]

CONFIG_FILE = "config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f: saved=json.load(f)
            return (saved.get("agentes",json.loads(json.dumps(DEFAULT_AGENTES))),
                    saved.get("turnos",json.loads(json.dumps(DEFAULT_TURNOS))),
                    saved.get("nums_excluidos",list(DEFAULT_NUMS_EXCLUIDOS)),
                    saved.get("ventana_cb",5), saved.get("modo_demo",False))
        except: pass
    return (json.loads(json.dumps(DEFAULT_AGENTES)),json.loads(json.dumps(DEFAULT_TURNOS)),
            list(DEFAULT_NUMS_EXCLUIDOS),5,False)

def save_config():
    try:
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump({"agentes":st.session_state.cfg_agentes,"turnos":st.session_state.cfg_turnos,
                       "nums_excluidos":st.session_state.cfg_nums_excluidos,
                       "ventana_cb":st.session_state.cfg_ventana_cb,
                       "modo_demo":st.session_state.cfg_modo_demo},f,ensure_ascii=False,indent=2)
        return True
    except Exception as e: st.error(f"No se pudo guardar: {e}"); return False

# ── Temas
T = {"dark":{"bg":"#06080F","sidebar":"#090B14","card":"#0C0F1C","card2":"#0b1120","border":"rgba(255,255,255,.05)","border2":"rgba(255,255,255,.04)","text":"#C8D8E8","muted":"#2A4060","muted2":"#1A3050","muted3":"#0F2030","primary":"#5A9AEA","primary_dim":"#0F1A2E","primary_border":"rgba(60,120,220,.35)","green":"#22C55E","green_dim":"#166534","green_border":"rgba(34,197,94,.15)","red":"#EF4444","red_dim":"#7F1D1D","red_border":"rgba(239,68,68,.15)","yellow":"#EAB308","yellow_dim":"#92400E","plot_bg":"#06080F","grid":"rgba(255,255,255,.03)","bar_green":"#166534","bar_red":"#7F1D1D","bar_blue":"#1D4ED8","bar_dark":"#4A0404","input_bg":"#0F1525","scrollbar":"#1A2A40","tab":"#2A4060","tab_sel":"#5A9AEA","tab_sel_border":"#3A7ACA"},"light":{"bg":"#F0F4F8","sidebar":"#FFFFFF","card":"#FFFFFF","card2":"#F8FAFC","border":"rgba(0,0,0,.12)","border2":"rgba(0,0,0,.08)","text":"#0F172A","muted":"#334155","muted2":"#475569","muted3":"#64748B","primary":"#4F46E5","primary_dim":"#EEF2FF","primary_border":"rgba(79,70,229,.3)","green":"#16A34A","green_dim":"#14532D","green_border":"rgba(22,163,74,.25)","red":"#DC2626","red_dim":"#7F1D1D","red_border":"rgba(220,38,38,.22)","yellow":"#B45309","yellow_dim":"#78350F","plot_bg":"#FFFFFF","grid":"rgba(0,0,0,.09)","bar_green":"#16A34A","bar_red":"#DC2626","bar_blue":"#2563EB","bar_dark":"#7C3AED","input_bg":"#F8FAFC","scrollbar":"#CBD5E1","tab":"#64748B","tab_sel":"#4F46E5","tab_sel_border":"#4F46E5"}}

def get_css(c):
    is_light = c["bg"] != "#06080F"
    sidebar_text = c["muted"] if not is_light else c["text"]
    sidebar_label = c["muted2"] if not is_light else c["muted2"]
    df_bg = c["card"]
    df_text = c["text"]
    return f"""<style>@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{{font-family:'Outfit',sans-serif!important}}
.stApp{{background:{c['bg']}!important}}.stApp>header{{background:transparent!important}}
section[data-testid="stSidebar"]{{background:{c['sidebar']}!important;border-right:1px solid {c['border']}!important}}
section[data-testid="stSidebar"] *{{color:{sidebar_text}!important}}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] strong{{color:{c['text']}!important}}
section[data-testid="stSidebar"] label{{color:{sidebar_label}!important;font-size:11px!important;letter-spacing:.5px;text-transform:uppercase}}
section[data-testid="stSidebar"] input{{background:{c['input_bg']}!important;border:1px solid {c['primary_border']}!important;color:{c['text']}!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important}}
section[data-testid="stSidebar"] .stButton button{{width:100%;background:{c['primary_dim']}!important;border:1px solid {c['primary_border']}!important;color:{c['primary']}!important;font-weight:600!important}}
[data-testid="metric-container"]{{background:{c['card']}!important;border:1px solid {c['border']}!important;border-radius:12px!important;padding:16px 18px!important}}
[data-testid="stMetricLabel"]{{color:{c['muted']}!important;font-size:10px!important;letter-spacing:1.8px!important;text-transform:uppercase!important;font-family:'JetBrains Mono',monospace!important}}
[data-testid="stMetricValue"]{{color:{c['text']}!important;font-size:26px!important;font-weight:300!important}}
[data-testid="stMetricDelta"]{{font-size:11px!important}}
.stTabs [role="tablist"]{{border-bottom:1px solid {c['border']}!important;gap:4px}}
.stTabs [aria-selected="true"]{{border-bottom:2px solid {c['tab_sel_border']}!important}}
.stTabs [aria-selected="true"] button{{color:{c['tab_sel']}!important;font-weight:600}}
.stTabs [aria-selected="false"] button{{color:{c['tab']}!important}}
.stDataFrame{{background:{df_bg}!important}}
.stDataFrame {{color:{df_text}!important}}
.stTable{{background:{df_bg}!important}}
.stTable * {{color:{df_text}!important}}
hr{{border:1px solid {c['border']}!important}}
</style>"""

# ── Session State
if "cfg_agentes" not in st.session_state:
    agentes, turnos, nums_excl, vent_cb, demo = load_config()
    st.session_state.cfg_agentes = agentes
    st.session_state.cfg_turnos = turnos
    st.session_state.cfg_nums_excluidos = nums_excl
    st.session_state.cfg_ventana_cb = vent_cb
    st.session_state.cfg_modo_demo = demo

# ── Shortcuts
def get_agentes(): return st.session_state.cfg_agentes
def get_agentes_sin_central(): return {k:v for k,v in st.session_state.cfg_agentes.items() if not v.get("es_central")}
def get_central_id(): return next((k for k,v in st.session_state.cfg_agentes.items() if v.get("es_central")), "8668106")
def get_turnos(): return st.session_state.cfg_turnos
def get_nums_excluidos(): return st.session_state.cfg_nums_excluidos
AGENTES_SIN_ID = {"Sin turno", "Sin atender"}
END_REASONS = {"OK":"OK","CANCELLED":"Colgo","NO_ANSWER":"No respondio","TEMPORARILY_UNAVAILABLE":"No disponible","NOT_FOUND":"No encontrado","SERVICE_UNAVAILABLE":"Servicio no disponible","DECLINE":"Rechazada"}
ESC_RESPONSABLE = {"perdida","no_respondio","multiples_no_respuesta","colgo_timbrando"}
ESCENARIOS = {"atendida":{"es":"Atendida","color":"#22C55E"},"no_respondio":{"es":"No respondio","color":"#EF4444"},"colgo_timbrando":{"es":"Colgo timbrando","color":"#F59E0B"},"multiples_no_respuesta":{"es":"Multiples no respuesta","color":"#EF4444"},"rechazada":{"es":"Rechazada","color":"#EC4899"},"agente_no_disponible":{"es":"Agente no disponible","color":"#6366F1"},"no_enrutada":{"es":"No enrutada","color":"#6B7280"},"colgo_en_ivr":{"es":"Colgo en IVR","color":"#8B5CF6"},"perdida":{"es":"Perdida","color":"#EF4444"}}
fmt_dur = lambda s: f"{int(s)//60}m {int(s)%60}s" if s else "0s"
norm_num = lambda n: str(n or "").replace("+","").replace("-","").replace(" ","").replace("(","").replace(")","").strip()

# ── PAGE CONFIG
st.set_page_config(page_title="Dashboard CallMyWay", page_icon="", layout="wide", initial_sidebar_state="expanded")
st.markdown(get_css(T["dark"]), unsafe_allow_html=True)
c = T["dark"]
P = {"plot_bgcolor":c["plot_bg"],"paper_bgcolor":c["plot_bg"],"font":{"family":"Outfit","color":c["text"],"size":11},"xaxis":{"showgrid":False,"zeroline":False},"yaxis":{"showgrid":True,"gridwidth":1,"gridcolor":c["grid"],"zeroline":False},"margin":{"l":40,"r":20,"t":60,"b":40},"hovermode":"closest"}

now_lima = now_lima()
hoy_lima = now_lima

# ── API
PAGE_SIZE=1000; CHUNK_DAYS=10
def _fetch_chunk(ds,de):
    base={"username":_U,"password":_P,"format":"json","dateStart":ds,"dateEnd":de}
    all_cdrs,ini=[],0
    while True:
        r=requests.get("https://callmyway.com/getCdrs.php",params={**base,"ini":ini,"cant":PAGE_SIZE},timeout=30)
        r.raise_for_status(); data=r.json()
        page=data.get("cdrs",data) if isinstance(data,dict) else data
        if not page: break
        all_cdrs.extend(page)
        if len(page)<PAGE_SIZE: break
        ini+=PAGE_SIZE
    return all_cdrs

def fetch_cdrs(date_start=None,date_end=None,live=False,progress_cb=None):
    if live:
        try:
            r=requests.get("https://callmyway.com/getCdrs.php",params={"username":_U,"password":_P,"live":1,"fullAccount":1,"format":"json"},timeout=20)
            r.raise_for_status(); data=r.json()
            cdrs=data.get("cdrs",data) if isinstance(data,dict) else data
            return pd.DataFrame(cdrs or []),None
        except Exception as e: return None,str(e)
    try:
        dt_ini=datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S")
        dt_fin=datetime.strptime(date_end,  "%Y-%m-%d %H:%M:%S")
    except Exception as e: return None,f"Fechas invalidas: {e}"
    chunks,cursor=[],dt_ini
    while cursor<dt_fin:
        ce=min(cursor+timedelta(days=CHUNK_DAYS),dt_fin); chunks.append((cursor,ce)); cursor=ce
    all_cdrs=[]
    for i,(c_ini,c_fin) in enumerate(chunks):
        if progress_cb: progress_cb(i/len(chunks),f"Chunk {i+1}/{len(chunks)} · {c_ini.strftime('%d/%m')}→{c_fin.strftime('%d/%m')} · {len(all_cdrs):,} reg")
        try: all_cdrs.extend(_fetch_chunk(c_ini.strftime("%Y-%m-%d %H:%M:%S"),c_fin.strftime("%Y-%m-%d %H:%M:%S")))
        except: pass
    if progress_cb: progress_cb(1.0,f"Completado · {len(all_cdrs):,} registros")
    return (pd.DataFrame(all_cdrs) if all_cdrs else pd.DataFrame()),None

def clasificar_entrantes(df_inc):
    if df_inc is None or df_inc.empty: return pd.DataFrame()
    CENTRAL_ID=get_central_id(); agentes_reales=set(get_agentes_sin_central().keys())
    nums_excluidos={norm_num(n) for n in get_nums_excluidos()}
    df_inc=df_inc.copy()
    for col in ["dnis_user","ani_user","original_callid","ref_callid","ani","dnis"]:
        if col in df_inc.columns: df_inc[col]=df_inc[col].astype(str).str.strip().replace({"None":"","nan":"","null":"","<NA>":""})
    if nums_excluidos and "ani" in df_inc.columns:
        df_inc=df_inc[~df_inc["ani"].apply(norm_num).isin(nums_excluidos)]
    if df_inc.empty: return pd.DataFrame()
    df_trn=df_inc[df_inc["dnis_user"]==CENTRAL_ID]; df_ag=df_inc[df_inc["dnis_user"].isin(agentes_reales)]
    trn_by_ref={}
    for _,row in df_trn.iterrows():
        ref=str(row.get("ref_callid","")).strip()
        if ref: trn_by_ref[ref]=row
    ag_orig_set=set(df_ag["original_callid"].unique()) if not df_ag.empty else set()
    resultados=[]
    def _append(orig_cid,detect_time,ani_cliente,atendida,agente_id,duracion,ring_total,n_intentos,end_reason,escenario,agente_timbrando=None,espera_usuario=0):
        resultados.append({"original_callid":orig_cid,"detect_time":detect_time,"numero_cliente":ani_cliente,"atendida":atendida,"agente":get_agentes().get(str(agente_id),"Sin atender") if agente_id else "Sin atender","agente_id":agente_id,"agente_timbrando":get_agentes().get(str(agente_timbrando),"—") if agente_timbrando else "—","espera_usuario":max(0,int(espera_usuario or 0)),"duracion":duracion,"espera_total":ring_total,"n_intentos":n_intentos,"end_reason":end_reason,"end_reason_es":END_REASONS.get(end_reason,end_reason),"escenario":escenario,"escenario_es":esc_es(escenario),"hora":detect_time.hour if pd.notna(detect_time) else None,"fecha":detect_time.date() if pd.notna(detect_time) else None})
    for orig_cid,ag_grp in (df_ag.groupby("original_callid") if not df_ag.empty else []):
        trunk=trn_by_ref.get(orig_cid)
        if trunk is not None:
            ani_cliente=str(trunk.get("ani","—") or "—"); detect_time=min(trunk.get("detect_time"),ag_grp["detect_time"].min())
        else:
            ani_val=ag_grp["ani"].replace("",pd.NA).dropna(); ani_cliente=str(ani_val.iloc[0]) if not ani_val.empty else "—"
            detect_time=ag_grp["detect_time"].min()
        ring_total=int(ag_grp["ring_time"].apply(lambda x: max(0,int(x or 0))).sum()); n_intentos=len(ag_grp)
        contestado=ag_grp[ag_grp["duration"]>0]
        if not contestado.empty:
            best=contestado.loc[contestado["duration"].idxmax()]
            _append(orig_cid,detect_time,ani_cliente,True,str(best["dnis_user"]),int(best["duration"]),ring_total,n_intentos,str(best.get("end_reason","OK") or "OK"),"atendida")
        else:
            ers=ag_grp["end_reason"].replace("",pd.NA).dropna(); top_er=ers.mode().iloc[0] if not ers.empty else "UNKNOWN"
            if top_er=="CANCELLED": esc="colgo_timbrando"
            elif top_er in ("TEMPORARILY_UNAVAILABLE","NOT_FOUND","SERVICE_UNAVAILABLE"): esc="agente_no_disponible"
            elif top_er=="NO_ANSWER": esc="multiples_no_respuesta" if n_intentos>1 else "no_respondio"
            elif top_er=="DECLINE": esc="rechazada"
            else: esc="perdida"
            ag_timbrando=None
            if esc=="colgo_timbrando":
                ringing=ag_grp.sort_values("detect_time",ascending=False)
                ag_timbrando=str(ringing.iloc[0]["dnis_user"]) if not ringing.empty else None
            _append(orig_cid,detect_time,ani_cliente,False,None,0,ring_total,n_intentos,top_er,esc,agente_timbrando=ag_timbrando,espera_usuario=ring_total)
    for _,trn_row in (df_trn.iterrows() if not df_trn.empty else []):
        ref_cid=str(trn_row.get("ref_callid","")).strip()
        if ref_cid in ag_orig_set: continue
        orig_cid=str(trn_row.get("original_callid","")).strip()
        detect_time=trn_row.get("detect_time"); ani_cliente=str(trn_row.get("ani","—") or "—")
        er=str(trn_row.get("end_reason","UNKNOWN") or "UNKNOWN")
        esc="colgo_en_ivr" if er=="CANCELLED" else "agente_no_disponible" if er in ("TEMPORARILY_UNAVAILABLE","NOT_FOUND","SERVICE_UNAVAILABLE") else "no_enrutada"
        _append(orig_cid,detect_time,ani_cliente,False,None,0,0,0,er,esc)
    if not resultados: return pd.DataFrame()
    df=pd.DataFrame(resultados); df["agente_turno"]=df["detect_time"].apply(agente_de_turno)
    def calc_resp(r):
        if r["agente_turno"] in AGENTES_SIN_ID: return r["agente_turno"]
        return r["agente"] if r["atendida"] else r["agente_turno"]
    df["responsable"]=df.apply(calc_resp,axis=1)
    df.loc[df["agente_turno"].isin(AGENTES_SIN_ID),["atendida","agente"]]=[False,"Sin atender"]
    return df

def procesar(df_raw):
    if df_raw is None or df_raw.empty: return pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
    CENTRAL_ID=get_central_id(); todos_agentes=set(get_agentes().keys())
    df=df_raw.copy()
    for col in ["duration","ring_time"]: df[col]=pd.to_numeric(df.get(col,0),errors="coerce").fillna(0).astype(int)
    for col in ["detect_time","connect_time","disconnect_time"]:
        if col in df.columns: df[col]=pd.to_datetime(df[col].replace("",None),errors="coerce")
    for col in ["ani_user","dnis_user","ref_callid","original_callid"]:
        if col in df.columns: df[col]=df[col].astype(str).str.strip()
    if "type" not in df.columns: df["type"]=""
    df["type"]=df["type"].astype(str).replace({"None":"","nan":"","null":"","<NA>":""})
    mask_null=df["type"]==""
    if mask_null.any():
        df.loc[mask_null&df["dnis_user"].isin(todos_agentes),"type"]="incoming"
        df.loc[mask_null&df["ani_user"].isin(get_agentes_sin_central().keys())&~df["dnis_user"].isin(todos_agentes),"type"]="outgoing"
        df.loc[df["type"]=="","type"]="incoming"
    nums_excluidos={norm_num(n) for n in get_nums_excluidos()}
    mask_sal=(df["type"]=="outgoing")&(df["ani_user"].isin(get_agentes_sin_central().keys()))&(~df["dnis"].astype(str).str.startswith("833"))
    df_sal=df[mask_sal].copy()
    if nums_excluidos and "dnis" in df_sal.columns:
        df_sal=df_sal[~df_sal["dnis"].apply(lambda x: norm_num(str(x))).isin(nums_excluidos)]
    df_sal["agente"]=df_sal["ani_user"].map(get_agentes()); df_sal["numero_cliente"]=df_sal["dnis"].astype(str)
    df_sal["atendida"]=df_sal["duration"]>0; df_sal["hora"]=df_sal["detect_time"].dt.hour
    df_sal["fecha"]=df_sal["detect_time"].dt.date; df_sal["end_reason_es"]=df_sal["end_reason"].map(END_REASONS).fillna(df_sal["end_reason"])
    df_sal["agente_id"]=df_sal["ani_user"]
    df_ent=clasificar_entrantes(df[df["type"]=="incoming"].copy())
    return df_ent,df_sal,df

def calcular_cumplimiento(df_ent,df_sal):
    if df_ent is None or df_ent.empty or "escenario" not in df_ent.columns: return pd.DataFrame()
    ventana=pd.Timedelta(minutes=st.session_state.cfg_ventana_cb)
    perdidas=df_ent[(df_ent["atendida"]==False)&(df_ent["escenario"].isin(ESC_RESPONSABLE))].copy().sort_values("detect_time")
    if perdidas.empty: return pd.DataFrame()
    df_sal2=df_sal.copy() if not df_sal.empty else pd.DataFrame()
    if not df_sal2.empty and "dnis" in df_sal2.columns:
        df_sal2["_num"]=df_sal2["dnis"].apply(norm_num)
    df_ent2=df_ent.copy() if not df_ent.empty else pd.DataFrame()
    if not df_ent2.empty and "numero_cliente" in df_ent2.columns:
        df_ent2["_num"]=df_ent2["numero_cliente"].apply(norm_num)
    resultados=[]
    for _,row in perdidas.iterrows():
        t0=row["detect_time"]
        if pd.isna(t0): continue
        num=norm_num(row["numero_cliente"]); t_lim=t0+ventana
        cb_sal=pd.DataFrame()
        if not df_sal2.empty and "detect_time" in df_sal2.columns:
            cb_sal=df_sal2[(df_sal2["_num"]==num)&(df_sal2["detect_time"]>t0)&(df_sal2["detect_time"]<=t_lim)&(df_sal2["atendida"]==True)]
        cb_ent=pd.DataFrame()
        if "detect_time" in df_ent2.columns:
            cb_ent=df_ent2[(df_ent2["_num"]==num)&(df_ent2["detect_time"]>t0)&(df_ent2["detect_time"]<=t_lim)&(df_ent2["atendida"]==True)]
        if not cb_sal.empty:
            tipo="Agente llamo"; t_cb=cb_sal["detect_time"].min(); ag_cb=cb_sal.iloc[0].get("agente","—"); seg=int((t_cb-t0).total_seconds())
        elif not cb_ent.empty:
            tipo="Cliente volvio"; t_cb=cb_ent["detect_time"].min(); ag_cb=cb_ent.iloc[0].get("agente","—"); seg=int((t_cb-t0).total_seconds())
        else:
            tipo="Sin resolucion"; ag_cb="—"; seg=None
        resultados.append({"Fecha/Hora":t0,"Numero":row["numero_cliente"],"Responsable":row.get("responsable","—"),"Escenario":esc_es(row.get("escenario","")),"Resolucion":tipo,"Tiempo respuesta":fmt_dur(seg) if seg is not None else f"> {st.session_state.cfg_ventana_cb} min","Agente resolvio":ag_cb,"Cumplimiento":tipo!="Sin resolucion","_seg":seg})
    return pd.DataFrame(resultados)

def detectar_eventos_login_logout(df_sal):
    if df_sal is None or df_sal.empty:
        return pd.DataFrame()
    eventos = df_sal[df_sal["numero_cliente"].astype(str).isin(["*34", "*33"])].copy()
    if eventos.empty:
        return pd.DataFrame()
    eventos["tipo_evento"] = eventos["numero_cliente"].map({"*34": "LOGIN", "*33": "LOGOUT"})
    eventos = eventos.sort_values("detect_time", ascending=False)
    return eventos[["detect_time", "agente", "agente_id", "numero_cliente", "tipo_evento", "duracion"]]

def calcular_sesiones_agente(df_sal, agent_id):
    if df_sal is None or df_sal.empty:
        return []
    eventos = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))].copy().sort_values("detect_time")
    if eventos.empty:
        return []
    sesiones = []
    login_time = None
    for idx, evt in eventos.iterrows():
        if "*34" in str(evt.get("numero_cliente", "")):
            login_time = evt["detect_time"]
        elif "*33" in str(evt.get("numero_cliente", "")) and login_time:
            logout_time = evt["detect_time"]
            duracion_segundos = (logout_time - login_time).total_seconds()
            duracion_minutos = int(duracion_segundos / 60)
            llamadas_sesion = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["detect_time"] >= login_time) & (df_sal["detect_time"] <= logout_time) & (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))]
            llamadas_count = len(llamadas_sesion)
            llamadas_atendidas = (llamadas_sesion["atendida"] == True).sum()
            sesiones.append({"fecha": login_time.date(), "login": login_time, "logout": logout_time, "duracion_minutos": duracion_minutos, "llamadas_totales": llamadas_count, "llamadas_atendidas": llamadas_atendidas, "llamadas_no_atendidas": llamadas_count - llamadas_atendidas, "duracion_promedio_llamada": 0 if llamadas_count == 0 else duracion_segundos / llamadas_count})
            login_time = None
    if login_time:
        logout_time = now_lima
        duracion_segundos = (logout_time - login_time).total_seconds()
        duracion_minutos = int(duracion_segundos / 60)
        llamadas_sesion = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["detect_time"] >= login_time) & (df_sal["detect_time"] <= logout_time) & (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))]
        llamadas_count = len(llamadas_sesion)
        llamadas_atendidas = (llamadas_sesion["atendida"] == True).sum()
        sesiones.append({"fecha": login_time.date(), "login": login_time, "logout": None, "duracion_minutos": duracion_minutos, "llamadas_totales": llamadas_count, "llamadas_atendidas": llamadas_atendidas, "llamadas_no_atendidas": llamadas_count - llamadas_atendidas, "duracion_promedio_llamada": 0 if llamadas_count == 0 else duracion_segundos / llamadas_count, "activa": True})
    return sesiones

def obtener_estado_actual_agente(df_sal, agent_id):
    if df_sal is None or df_sal.empty:
        return {"estado": "Desconocido", "desde": None, "duracion": "—"}
    eventos = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))].copy().sort_values("detect_time", ascending=False)
    if eventos.empty:
        return {"estado": "Desconocido", "desde": None, "duracion": "—"}
    ultimo_evento = eventos.iloc[0]
    es_login = "*34" in str(ultimo_evento.get("numero_cliente", ""))
    if es_login:
        duracion_min = int((now_lima - ultimo_evento["detect_time"]).total_seconds() / 60)
        horas = duracion_min // 60
        minutos = duracion_min % 60
        return {"estado": "Online", "desde": ultimo_evento["detect_time"], "duracion": f"{horas}h {minutos}m"}
    else:
        return {"estado": "Offline", "desde": ultimo_evento["detect_time"], "duracion": "—"}

def calcular_metricas_supervisor(df_sal, df_ent, agent_id):
    if df_sal is None or df_sal.empty:
        return {}
    hoy = now_lima.date()
    sesiones = calcular_sesiones_agente(df_sal, agent_id)
    sesiones_hoy = [s for s in sesiones if s["fecha"] == hoy]
    llamadas_hoy = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["detect_time"].dt.date == hoy) & (~df_sal["numero_cliente"].astype(str).isin(["*34", "*33"]))]
    llamadas_atendidas = (llamadas_hoy["atendida"] == True).sum()
    llamadas_no_atendidas = len(llamadas_hoy) - llamadas_atendidas
    duracion_promedio = int(llamadas_hoy["duracion"].mean()) if len(llamadas_hoy) > 0 else 0
    tiempo_conectado = sum([s["duracion_minutos"] for s in sesiones_hoy])
    horas_conectado = tiempo_conectado / 60
    productividad = len(llamadas_hoy) / horas_conectado if horas_conectado > 0 else 0
    pausas = []
    if len(sesiones_hoy) > 0:
        for sesion in sesiones_hoy:
            llamadas_sesion = df_sal[(df_sal["agente_id"] == agent_id) & (df_sal["detect_time"] >= sesion["login"]) & (df_sal["detect_time"] <= (sesion["logout"] or now_lima))].copy().sort_values("detect_time")
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
    return {"llamadas_totales": len(llamadas_hoy), "llamadas_atendidas": llamadas_atendidas, "llamadas_no_atendidas": llamadas_no_atendidas, "duracion_promedio_llamada": duracion_promedio, "tiempo_conectado_minutos": tiempo_conectado, "productividad_llamadas_por_hora": round(productividad, 2), "pausas": pausas, "descansos": descansos, "sesiones_hoy": len(sesiones_hoy)}

def esc_es(k): return ESCENARIOS.get(k,{}).get("es",k)
def esc_color(k): return ESCENARIOS.get(k,{}).get("color","#6B7280")
def agente_de_turno(dt):
    dow,h=dt.weekday(),dt.hour; h_ext=h if h>=6 else h+24
    for t in get_turnos():
        if dow in t["dias"] and t["h_ini"]<=h_ext<t["h_fin"]: return t["agente"]
    dow_prev=(dow-1)%7
    for t in get_turnos():
        if dow_prev in t["dias"] and t["h_ini"]<=h_ext<t["h_fin"]: return t["agente"]
    return "Sin turno"

# ── UI: Sidebar
with st.sidebar:
    st.markdown("# Dashboard CallMyWay")
    tab_cfg = st.tabs(["Dashboard", "Agentes", "Turnos", "Exclusiones", "DID", "General"])
    with tab_cfg[0]:
        st.markdown("**Rango de fechas**")
        col_f1, col_f2 = st.columns(2)
        with col_f1: df_start = st.date_input("Desde", value=(now_lima-timedelta(days=7)).date())
        with col_f2: df_end = st.date_input("Hasta", value=now_lima.date())
        try:
            dt_start = datetime.combine(df_start, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
            dt_end = datetime.combine(df_end, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
        except: dt_start, dt_end = None, None
    with tab_cfg[1]:
        st.markdown("**Agentes**")
        for aid, info in st.session_state.cfg_agentes.items():
            if info.get("es_central"): continue
            col_a, col_e = st.columns([4, 1])
            with col_a: st.session_state.cfg_agentes[aid]["nombre"] = st.text_input(f"ID {aid}", value=info["nombre"], key=f"nombre_{aid}", label_visibility="collapsed")
            with col_e: st.session_state.cfg_agentes[aid]["activo"] = st.checkbox("", value=info.get("activo", True), key=f"activo_{aid}", label_visibility="collapsed")
    with tab_cfg[2]:
        st.markdown("**Turnos**")
        for i, t in enumerate(st.session_state.cfg_turnos):
            st.markdown(f"**Turno {i+1}**")
            col_a, col_b = st.columns(2)
            with col_a: st.session_state.cfg_turnos[i]["agente"] = st.text_input(f"Agente {i}", value=t["agente"], key=f"turno_agente_{i}", label_visibility="collapsed")
            with col_b: st.session_state.cfg_turnos[i]["h_ini"] = st.number_input(f"Inicio {i}", value=t["h_ini"], min_value=0, max_value=30, key=f"turno_hini_{i}", label_visibility="collapsed")
    with tab_cfg[3]:
        st.markdown("**Numeros excluidos**")
        nums_txt = st.text_area("Un numero por linea", value="\n".join(get_nums_excluidos()), height=100)
        st.session_state.cfg_nums_excluidos = [n.strip() for n in nums_txt.split("\n") if n.strip()]
    with tab_cfg[4]:
        st.markdown("**DID / Campanas**")
        st.info("Configuracion DID aqui")
    with tab_cfg[5]:
        st.markdown("**General**")
        st.session_state.cfg_ventana_cb = st.slider("Ventana CB (min)", value=st.session_state.cfg_ventana_cb, min_value=1, max_value=60)
        st.session_state.cfg_modo_demo = st.checkbox("Modo demo", value=st.session_state.cfg_modo_demo)
        if st.button("Guardar configuracion"):
            if save_config(): st.success("Guardado!")

# ── LOAD DATA
st.markdown("# Dashboard CallMyWay")
st.markdown(f"**Ultima actualizacion:** {now_lima.strftime('%Y-%m-%d %H:%M:%S')} (Lima)")

if dt_start and dt_end:
    pb = st.progress(0)
    def cb_progress(pct, msg): pb.progress(int(pct*100)); st.caption(msg)
    df_raw, err = fetch_cdrs(dt_start, dt_end, live=False, progress_cb=cb_progress)
    if err:
        st.error(f"Error: {err}")
        df_raw = None
else:
    st.warning("Selecciona rango de fechas")
    df_raw = None

if df_raw is not None and not df_raw.empty:
    df_ent, df_sal, df_raw_full = procesar(df_raw)
    df_cb_kpi = calcular_cumplimiento(df_ent, df_sal)
else:
    df_ent, df_sal, df_raw_full = pd.DataFrame(), pd.DataFrame(), None
    df_cb_kpi = pd.DataFrame()

# ── TABS
tab_overview, tab_ent, tab_sal, tab_ag, tab_turnos, tab_seg, tab_cl, tab_sup, tab_raw_t = st.tabs([
    "Overview", "Entrantes", "Salientes", "Agentes", "Turnos", "Seguimiento", "Clientes", "Supervision", "Raw"
])

with tab_overview:
    st.markdown("#### Overview - KPIs Principales")
    if not df_ent.empty:
        tot_ent = len(df_ent); atd = int((df_ent["atendida"]==True).sum()); perd = tot_ent - atd; pct_at = round(atd/tot_ent*100) if tot_ent else 0
        dur_prom = int(df_ent[df_ent["atendida"]==True]["duracion"].mean()) if (df_ent["atendida"]==True).sum()>0 else 0
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Entrantes", f"{tot_ent:,}")
        col2.metric("Atendidas", f"{atd:,}", f"{pct_at}%")
        col3.metric("Perdidas", f"{perd:,}", f"{100-pct_at}%")
        col4.metric("% Atencion", f"{pct_at}%")
        col5.metric("Dur. promedio", fmt_dur(dur_prom))
        if not df_sal.empty: col6.metric("Salientes", f"{len(df_sal):,}")
        st.markdown("---")
        if "hora" in df_ent.columns:
            por_hora = df_ent.groupby("hora").agg(total=("numero_cliente","count"), atendidas=("atendida","sum")).reset_index()
            fig_hora = px.bar(por_hora, x="hora", y=["total","atendidas"], title="Llamadas por hora", barmode="group")
            fig_hora.update_layout(height=300, **P)
            st.plotly_chart(fig_hora, use_container_width=True)

with tab_ent:
    st.markdown("#### Historico - Entrantes")
    if df_ent.empty: st.info("Sin datos")
    else:
        busq = st.text_input("Buscar numero")
        df_ent_f = df_ent.copy()
        if busq: df_ent_f = df_ent_f[df_ent_f["numero_cliente"].astype(str).str.contains(busq, na=False)]
        cols_e = ["detect_time","numero_cliente","agente","atendida","duracion","responsable"]
        cols_e = [c for c in cols_e if c in df_ent_f.columns]
        st.dataframe(df_ent_f[cols_e], use_container_width=True, hide_index=True)

with tab_sal:
    st.markdown("#### Historico - Salientes")
    if df_sal.empty: st.info("Sin datos")
    else:
        busq = st.text_input("Buscar", key="busq_sal")
        df_sal_f = df_sal.copy()
        if busq: df_sal_f = df_sal_f[df_sal_f["numero_cliente"].astype(str).str.contains(busq, na=False)]
        cols_s = ["detect_time","agente","numero_cliente","atendida","duracion"]
        cols_s = [c for c in cols_s if c in df_sal_f.columns]
        st.dataframe(df_sal_f[cols_s], use_container_width=True, hide_index=True)

with tab_ag:
    st.markdown("#### Agentes - Desempeño")
    ag_rows = []
    for resp in sorted(df_ent["responsable"].dropna().unique() if not df_ent.empty else []):
        sub = df_ent[df_ent["responsable"]==resp]
        tot = len(sub); at = int((sub["atendida"]==True).sum()); dr = int(sub["duracion"].mean()) if len(sub)>0 else 0
        ag_rows.append({"Agente": resp, "Total": tot, "Atendidas": at, "Perdidas": tot-at, "% At": f"{round(at/tot*100) if tot else 0}%", "Dur. Prom": fmt_dur(dr)})
    if ag_rows:
        df_ag = pd.DataFrame(ag_rows)
        st.dataframe(df_ag, use_container_width=True, hide_index=True)

with tab_turnos:
    st.markdown("#### Turnos - Cobertura")
    turnos_list = []
    for t in get_turnos():
        dia_txt = ",".join(["L","M","X","J","V","S","D"][d] for d in t["dias"])
        turnos_list.append({"Dias": dia_txt, "Inicio": t["h_ini"], "Fin": t["h_fin"], "Agente": t["agente"]})
    if turnos_list:
        df_turnos = pd.DataFrame(turnos_list)
        st.dataframe(df_turnos, use_container_width=True, hide_index=True)

with tab_seg:
    st.markdown("#### Seguimiento")
    if df_cb_kpi.empty: st.info("Sin seguimiento")
    else:
        total = len(df_cb_kpi); cumpl = int(df_cb_kpi["Cumplimiento"].sum()); no_cumpl = total - cumpl; pct = round(cumpl/total*100) if total else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Pendientes", total)
        col2.metric("Resueltos", f"{cumpl} ({pct}%)")
        col3.metric("Sin resolver", no_cumpl)
        st.dataframe(df_cb_kpi.drop(columns=["Cumplimiento","_seg"], errors="ignore"), use_container_width=True, height=350, hide_index=True)

with tab_cl:
    st.markdown("#### Clientes - Problematicos")
    if df_ent.empty: st.info("Sin datos")
    else:
        cl = df_ent.groupby("numero_cliente").agg(total=("numero_cliente","count"), atendidas=("atendida","sum")).reset_index()
        cl["perdidas"] = cl["total"] - cl["atendidas"]
        cp = cl[cl["perdidas"]>=2].sort_values("perdidas", ascending=False).head(10)
        if not cp.empty:
            for _, row in cp.iterrows():
                st.markdown(f"**{row['numero_cliente']}** - {int(row['perdidas'])} perdidas de {int(row['total'])}")

with tab_sup:
    st.markdown("#### Supervision de Agentes")
    eventos = detectar_eventos_login_logout(df_sal)
    sup_tab1, sup_tab2, sup_tab3 = st.tabs(["Estado Actual", "Metricas Hoy", "Historial"])
    
    with sup_tab1:
        st.markdown("**Estado Actual de Conexion**")
        agentes_cols = st.columns(3)
        col_idx = 0
        for aid, info in sorted(st.session_state.cfg_agentes.items()):
            if info.get("es_central"): continue
            col = agentes_cols[col_idx % 3]; col_idx += 1
            estado_info = obtener_estado_actual_agente(df_sal, aid)
            estado_txt = estado_info["estado"]
            duracion_txt = estado_info["duracion"]
            desde_txt = estado_info["desde"].strftime("%H:%M") if estado_info["desde"] else "—"
            if "Online" in estado_txt: color_fondo = c["green_border"]; icon = "Online"
            elif "Offline" in estado_txt: color_fondo = c["red_border"]; icon = "Offline"
            else: color_fondo = c["border"]; icon = "Unknown"
            with col:
                st.markdown(f"<div style='background:{c['card']};border:2px solid {color_fondo};border-radius:12px;padding:16px;text-align:center'><div style='font-size:28px;margin-bottom:8px'>{icon}</div><div style='color:{c['text']};font-weight:600;margin-bottom:8px'>{info['nombre']}</div><div style='color:{c['muted']};font-size:11px'><div>Desde: {desde_txt}</div><div>Duracion: {duracion_txt}</div></div></div>", unsafe_allow_html=True)
    
    with sup_tab2:
        st.markdown("**Metricas de Hoy por Agente**")
        metricas_rows = []
        for aid, info in st.session_state.cfg_agentes.items():
            if info.get("es_central"): continue
            metr = calcular_metricas_supervisor(df_sal, df_ent, aid)
            if not metr: continue
            estado_info = obtener_estado_actual_agente(df_sal, aid)
            estado_icon = "Online" if "Online" in estado_info["estado"] else "Offline" if "Offline" in estado_info["estado"] else "Unknown"
            metricas_rows.append({"Estado": estado_icon, "Agente": info["nombre"], "Llamadas": metr.get("llamadas_totales", 0), "Atendidas": metr.get("llamadas_atendidas", 0), "Dur.Prom": f"{metr.get('duracion_promedio_llamada', 0)}s", "Conectado": f"{metr.get('tiempo_conectado_minutos', 0)}m", "Productividad": f"{metr.get('productividad_llamadas_por_hora', 0):.1f}c/h"})
        if metricas_rows:
            df_metricas = pd.DataFrame(metricas_rows)
            st.dataframe(df_metricas, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("Sin datos de supervision disponibles")
    
    with sup_tab3:
        st.markdown("**Historial de Login/Logout - Hoy**")
        if not eventos.empty:
            eventos_hoy = eventos[eventos["detect_time"].dt.date == now_lima.date()].copy()
            if not eventos_hoy.empty:
                hist_rows = []
                for _, evt in eventos_hoy.iterrows():
                    hist_rows.append({"Hora": evt["detect_time"].strftime("%H:%M:%S"), "Agente": evt["agente"], "Evento": evt["tipo_evento"], "Codigo": evt["numero_cliente"]})
                df_hist = pd.DataFrame(hist_rows)
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                st.download_button("Exportar Historial", data=df_hist.to_csv(index=False).encode("utf-8-sig"), file_name=f"supervision_{now_lima.strftime('%Y%m%d')}.csv", mime="text/csv")
            else:
                st.info("Sin eventos de login/logout registrados hoy")
        else:
            st.info("Sin datos de login/logout disponibles")

with tab_raw_t:
    st.markdown("#### Registros sin procesar")
    if df_raw_full is not None and not df_raw_full.empty:
        busq_r=st.text_input("Buscar",key="busq_raw")
        dr=df_raw_full.copy()
        if busq_r:
            mask=pd.Series([False]*len(dr))
            for cx in ["ani","dnis","callid","original_callid","ani_user","dnis_user"]:
                if cx in dr.columns: mask|=dr[cx].astype(str).str.contains(busq_r,case=False,na=False)
            dr=dr[mask]
        cols_r=[cx for cx in ["detect_time","type","ani","dnis","ani_user","dnis_user","duration","ring_time","end_reason","connect_time","original_callid"] if cx in dr.columns]
        rs1,rs2,rs3,rs4=st.columns(4)
        rs1.metric("Total",f"{len(df_raw_full):,}"); rs2.metric("Dur>0",f"{int((df_raw_full['duration']>0).sum()):,}" if "duration" in df_raw_full.columns else "—")
        rs3.metric("Incoming",f"{int((df_raw_full['type']=='incoming').sum()):,}" if "type" in df_raw_full.columns else "—")
        rs4.metric("Outgoing",f"{int((df_raw_full['type']=='outgoing').sum()):,}" if "type" in df_raw_full.columns else "—")
        st.dataframe(dr[cols_r],use_container_width=True,height=460,hide_index=True)
        st.download_button("Exportar raw",data=dr[cols_r].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"raw_{hoy_lima.strftime('%Y%m%d_%H%M')}.csv",mime="text/csv")
