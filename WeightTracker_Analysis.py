import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# Fix encoding Windows
sys.stdout.reconfigure(encoding='utf-8')

TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "2f985638dc5b80ce8503c3b8eca50374"
URL = "https://app.notion.com/p/2f985638dc5b80ce8503c3b8eca50374?v=2f985638dc5b80e498b8000cceedc1b2"
DATABASE_ID2="37685638dc5b8099abe1e28621a04f5b"
URL2="https://app.notion.com/p/37685638dc5b8099abe1e28621a04f5b?v=37685638dc5b8072a7d3000cec865882"

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

res = requests.post(url, headers=headers, json={
    "sorts": [{"property": "Fecha_inicio", "direction": "ascending"}]
})
filas = res.json()["results"]

datos = []
for fila in filas:
    p = fila["properties"]
    if not p["Fecha_inicio"]["date"]:
        continue
    obs_lista = p["Observaciones "]["rich_text"]
    
    datos.append({
        "fecha":            datetime.strptime(p["Fecha_inicio"]["date"]["start"], "%Y-%m-%d"),
        "peso":             p["Peso_kg"]["number"] or 0,
        "gym":              p["Dias_Gym"]["number"] or 0,
        "pasos":            p["Pasos_med_diarios"]["number"] or 0,
        "cardio":           p["Dias_Cardio"]["number"] or 0,
        "sueno":            p["Sueño_medio_h"]["number"] or 0,
        "bienestar":        p["Bienestar(1-5)"]["number"] or 0,
        "activ_strava_min": p["Activ_Strava_min"]["number"] or 0,
        "activ_gym_min":    p["Activ_Gym_min"]["number"] or 0,
        "dias_strava":      p["Dias_Strava"]["number"] or 0,
        "esfuerzo_gym":     p["Esfuerzo_Gym(1-10)"]["number"] or 0,
        "obs":              obs_lista[0]["plain_text"] if obs_lista else "",
    })

fechas = [d["fecha"] for d in datos]
pesos  = [d["peso"]  for d in datos]
gyms   = [d["gym"]   for d in datos]
pasos  = [d["pasos"] for d in datos]
n = len(pesos)

x = np.arange(n)
m, b = np.polyfit(x, pesos, 1)

peso_actual  = pesos[-1]
perdida      = round(pesos[0] - pesos[-1], 1)
peso_min     = min(pesos)
pasos_medio  = round(sum(pasos) / n) if n > 0 else 0

pred_fechas = [fechas[-1] + timedelta(weeks=i+1) for i in range(12)]
pred_pesos  = [round(m*(n+i) + b, 2) for i in range(12)]
pred_hi     = [round(v+0.5, 2) for v in pred_pesos]
pred_lo     = [round(v-0.5, 2) for v in pred_pesos]

# ── PALETA DE COLORES ────────────────────────────────────────────────────────
C_BLUE   = '#185FA5'
C_TEAL   = '#1D9E75'
C_AMBER  = '#BA7517'
C_GRAY   = '#888780'
C_BG     = '#FAFAFA'
C_BORDER = '#E4E2DA'
FONT = 'DM Sans, Arial'

fig = go.Figure()

# Banda de incertidumbre predicción
fig.add_trace(go.Scatter(
    x=pred_fechas + pred_fechas[::-1],
    y=pred_hi + pred_lo[::-1],
    fill='toself',
    fillcolor='rgba(29,158,117,0.08)',
    line=dict(color='rgba(0,0,0,0)'),
    name='Intervalo ±0.5 kg',
    hoverinfo='skip',
    visible=False,
))

# Línea de peso real
fig.add_trace(go.Scatter(
    x=fechas, y=pesos,
    mode='lines+markers',
    name='Peso real',
    line=dict(color=C_BLUE, width=2.5, shape='spline', smoothing=0.8),
    marker=dict(size=6, color=C_BLUE, line=dict(color='white', width=1.5)),
    customdata=[d["obs"] for d in datos],
    hovertemplate='<b>%{x|%d %b}</b><br>Peso: <b>%{y} kg</b><br><i>%{customdata}</i><extra></extra>',
))

# Días de gym en eje secundario
fig.add_trace(go.Scatter(
    x=fechas, y=gyms,
    mode='lines+markers',
    name='Dias gym',
    line=dict(color=C_AMBER, width=1.5, shape='spline', smoothing=0.6, dash='dot'),
    marker=dict(size=4, color=C_AMBER),
    yaxis='y2',
    visible=False,
))

# Pasos medios en eje secundario
fig.add_trace(go.Scatter(
    x=fechas, y=pasos,
    mode='lines+markers',
    name='Pasos medios',
    line=dict(color=C_TEAL, width=1.5, shape='spline', smoothing=0.6, dash='dash'),
    marker=dict(size=4, color=C_TEAL),
    yaxis='y2',
    visible=False,
))

# Línea de predicción
fig.add_trace(go.Scatter(
    x=[fechas[-1]] + pred_fechas,
    y=[pesos[-1]]  + pred_pesos,
    mode='lines+markers',
    name='Prediccion',
    line=dict(color=C_TEAL, width=2, shape='spline', smoothing=0.6, dash='dash'),
    marker=dict(size=5, color=C_TEAL, line=dict(color='white', width=1)),
    hovertemplate='<b>%{x|%d %b}</b><br>Pred: <b>%{y} kg</b><extra></extra>',
    visible=False,
))

# ── LÍNEAS DE OBJETIVO Y ZONAS ───────────────────────────────────────────────
fig.add_hline(y=80, line_width=1.5, line_color="#E55C5C", line_dash="solid", opacity=0.8,
              annotation_text="Peligro", annotation_position="top left", 
              annotation_font_color="#E55C5C", annotation_font_size=10)

fig.add_hline(y=74, line_width=1.5, line_color="#F2994A", line_dash="solid", opacity=0.8,
              annotation_text="Deseado Alto", annotation_position="top left", 
              annotation_font_color="#F2994A", annotation_font_size=10)

fig.add_hline(y=72, line_width=1.5, line_color="#F2C94C", line_dash="solid", opacity=0.8,
              annotation_text="Deseado Bajo", annotation_position="top left", 
              annotation_font_color="#E0B020", annotation_font_size=10)

fig.add_hline(y=70, line_width=1.5, line_color="#27AE60", line_dash="solid", opacity=0.8,
              annotation_text="Objetivo", annotation_position="top left", 
              annotation_font_color="#27AE60", annotation_font_size=10)

# ── BOTONES DE VISTA ─────────────────────────────────────────────────────────
buttons = [
    dict(label='Peso',         method='update', args=[{'visible': [False, True,  False, False, False]}]),
    dict(label='+ Gym',        method='update', args=[{'visible': [False, True,  True,  False, False]}]),
    dict(label='+ Pasos',      method='update', args=[{'visible': [False, True,  False, True,  False]}]),
    dict(label='Prediccion',   method='update', args=[{'visible': [True,  True,  False, False, True ]}]),
    dict(label='Todo',         method='update', args=[{'visible': [True,  True,  True,  True,  True ]}]),
]

fig.update_layout(
    updatemenus=[dict(
        type='buttons', direction='right',
        x=0.0, y=1.12, xanchor='left', yanchor='bottom',
        buttons=buttons,
        bgcolor='#EFEFEB', bordercolor=C_BORDER, borderwidth=1,
        font=dict(size=12, family=FONT, color='#444441'),
        pad=dict(r=4, t=4, b=4),
    )],
    yaxis=dict(
        title='', 
        range=[69, 81],
        showgrid=True, gridcolor='#EEECEA', gridwidth=1,
        zeroline=False, tickfont=dict(size=11, color=C_GRAY), ticksuffix=' kg',
    ),
    yaxis2=dict(
        overlaying='y', side='right', showgrid=False,
        tickfont=dict(size=11, color=C_GRAY), zeroline=False,
    ),
    xaxis=dict(
        showgrid=False, tickformat='%d %b', tickfont=dict(size=11, color=C_GRAY),
        tickangle=-40, zeroline=False,
    ),
    hovermode='x unified',
    hoverlabel=dict(bgcolor='white', bordercolor=C_BORDER, font=dict(size=12, family=FONT)),
    legend=dict(orientation='h', y=-0.22, font=dict(size=12, family=FONT, color='#444'), bgcolor='rgba(0,0,0,0)'),
    margin=dict(t=80, b=90, l=60, r=60),
    plot_bgcolor=C_BG, paper_bgcolor=C_BG, font=dict(family=FONT, size=12),
)

# ── CÁLCULO DE KPIs ──────────────────────────────────────────────────────────
# KPIs Generales / Históricos
ultima4       = pesos[-4:] if n >= 4 else pesos
diff_4semanas = round(ultima4[-1] - ultima4[0], 1) if len(ultima4) > 1 else 0
ritmo_semana  = round((pesos[-1] - pesos[0]) / (n - 1), 2) if n > 1 else 0
    
media_gym     = round(sum(gyms) / n, 1) if n > 0 else 0
media_sueno   = round(sum(item["sueno"] for item in datos) / n, 1) if n > 0 else 0
media_strava  = round(sum(item["dias_strava"] for item in datos) / n, 1) if n > 0 else 0

# KPIs: Media de las últimas 4 semanas
ultimos_datos = datos[-4:] if n >= 4 else datos
n_ultimos     = len(ultimos_datos)

media_gym_4s    = round(sum(gyms[-4:]) / n_ultimos, 1) if n_ultimos > 0 else 0
media_strava_4s = round(sum(item["dias_strava"] for item in ultimos_datos) / n_ultimos, 1) if n_ultimos > 0 else 0
pasos_medio_4s  = round(sum(pasos[-4:]) / n_ultimos) if n_ultimos > 0 else 0
media_sueno_4s  = round(sum(item["sueno"] for item in ultimos_datos) / n_ultimos, 1) if n_ultimos > 0 else 0
    
signo = '+' if diff_4semanas > 0 else ''

# ── LÓGICA DE COLORES PARA COMPARACIÓN ───────────────────────────────────────
def obtener_color_comparacion(val_reciente, val_historico):
    if val_reciente > val_historico:
        return "#27AE60"  # Verde
    elif val_reciente < val_historico:
        return "#E55C5C"  # Rojo
    else:
        return "#F2994A"  # Naranja

color_gym    = obtener_color_comparacion(media_gym_4s, media_gym)
color_strava = obtener_color_comparacion(media_strava_4s, media_strava)
color_pasos  = obtener_color_comparacion(pasos_medio_4s, pasos_medio)
color_sueno  = obtener_color_comparacion(media_sueno_4s, media_sueno)

# ── HTML Y CSS PARA LOS KPIs ─────────────────────────────────────────────────
html_head = f'''
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    body {{ background: {C_BG}; margin: 0; padding: 24px; font-family: 'DM Sans', Arial, sans-serif; }}
    
    .kpi-container {{ 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
        gap: 16px; 
        margin-bottom: 24px; 
    }}
    
    .kpi-card {{
        background: white; border: 1px solid {C_BORDER}; border-radius: 8px;
        padding: 16px; display: flex; align-items: center; gap: 14px;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.04);
    }}
    
    .kpi-icon {{ font-size: 24px; }}
    .kpi-data {{ display: flex; flex-direction: column; }}
    .kpi-val {{ font-size: 18px; font-weight: 600; color: #2C2C2A; }}
    .kpi-label {{ font-size: 11px; letter-spacing: 0.05em; color: {C_GRAY}; text-transform: uppercase; margin-top: 4px; }}
    
    /* Clase para el subtexto base sin color predefinido, el color se inyecta por estilo inline */
    .kpi-subtext {{ font-size: 11px; margin-top: 4px; font-weight: 600; }}
    
    .main-svg {{ border-radius: 12px; }}
</style>
'''

html_kpis = f'''
<div class="kpi-container">
    <div class="kpi-card"><span class="kpi-icon">⚖️</span><div class="kpi-data"><span class="kpi-val">{peso_actual} kg</span><span class="kpi-label">Peso actual</span></div></div>
    <div class="kpi-card"><span class="kpi-icon">📉</span><div class="kpi-data"><span class="kpi-val">-{perdida} kg</span><span class="kpi-label">Pérdida total</span></div></div>
    <div class="kpi-card"><span class="kpi-icon">📅</span><div class="kpi-data"><span class="kpi-val">{signo}{diff_4semanas} kg</span><span class="kpi-label">Últ. 4 semanas</span></div></div>
    <div class="kpi-card"><span class="kpi-icon">📈</span><div class="kpi-data"><span class="kpi-val">{ritmo_semana} kg</span><span class="kpi-label">Ritmo/semana</span></div></div>
    
    <div class="kpi-card">
        <span class="kpi-icon">🏋️</span>
        <div class="kpi-data">
            <span class="kpi-val">{media_gym} días</span><span class="kpi-label">Gym (Media total)</span>
            <span class="kpi-subtext" style="color: {color_gym}">Últ. mes: {media_gym_4s} días</span>
        </div>
    </div>
    
    <div class="kpi-card">
        <span class="kpi-icon">🚴</span>
        <div class="kpi-data">
            <span class="kpi-val">{media_strava} días</span><span class="kpi-label">Strava (Media total)</span>
            <span class="kpi-subtext" style="color: {color_strava}">Últ. mes: {media_strava_4s} días</span>
        </div>
    </div>
    
    <div class="kpi-card">
        <span class="kpi-icon">👟</span>
        <div class="kpi-data">
            <span class="kpi-val">{pasos_medio:,}</span><span class="kpi-label">Pasos (Media total)</span>
            <span class="kpi-subtext" style="color: {color_pasos}">Últ. mes: {pasos_medio_4s:,}</span>
        </div>
    </div>
    
    <div class="kpi-card">
        <span class="kpi-icon">😴</span>
        <div class="kpi-data">
            <span class="kpi-val">{media_sueno} h</span><span class="kpi-label">Sueño (Media total)</span>
            <span class="kpi-subtext" style="color: {color_sueno}">Últ. mes: {media_sueno_4s} h</span>
        </div>
    </div>
</div>
'''

plot_html = fig.to_html(
    include_plotlyjs='cdn', 
    full_html=False,
    config={'displayModeBar': False, 'responsive': True},
    div_id='peso-chart',
    default_width='100%', 
    default_height='520px'
)

# ── ENSAMBLAR Y EXPORTAR ─────────────────────────────────────────────────────
final_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Peso</title>
    {html_head}
</head>
<body>
    {html_kpis}
    {plot_html}
</body>
</html>
'''

with open("peso.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Generado: peso.html")
