import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io
import xlsxwriter
import urllib.parse

# ==========================================
# 🎨 ZONA DE PERSONALIZACIÓN
# ==========================================
NOMBRE_EMPRESA = "Xingu CEO"
ICONO_APP = "🍇"
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

# --- ESTILO CSS PRO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #0E1117;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 3px solid #FF4B4B;
        color: #FF4B4B;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 700;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- SEGURIDAD (CON FIX DE ESPACIOS) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA} Cloud</h1>", unsafe_allow_html=True)
        st.write("")
        password = st.text_input("Senha / Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            try:
                pass_limpia = password.strip() # Elimina espacios fantasma
                if pass_limpia == st.secrets["passwords"]["admin_password"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("🚫 Incorrecto / Incorreto")
            except:
                st.error("⚠️ Error: Configura [passwords] en Secrets.")
    return False

# --- MAPA DE MESES ---
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

MONTHS_UI = {
    "Português": MESES_PT,
    "Español": {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"},
    "English": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
}

# --- IDIOMAS ---
TR = {
    "Português": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nova Venda", "🛠️ Admin", "📜 Log"],
        "headers": ["Inteligência de Negócios", "Registrar Venda", "Gestão", "Auditoria"],
        "metrics": ["Faturamento Total", "Volume (Kg)", "Comissão (2%)", "Ticket Médio", "Melhor Cliente"],
        "charts": ["Tendência (Diária)", "Mix de Produtos", "Vendas por Empresa"],
        "table_title": "Detalhamento de Vendas",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar Venda"],
        "actions": ["Salvar Edição", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk_label": "Gestão em Massa (Apagar Vários)",
        "clean_hist_label": "Limpeza de Histórico",
        "download_label": "📗 Exportar para Excel (.xlsx)",
        "logout_label": "🔒 Sair do Sistema",
        "goal_label": "🎯 Meta de", 
        "goal_save": "💾 Salvar Meta do Mês",
        "goal_text": "Progresso Mensal",
        "msgs": ["Venda Registrada!", "Apagado com sucesso!", "Sem dados", "Meta Atualizada!"],
        "new_labels": ["Nome Cliente:", "Nome Produto:"],
        "col_map": {"Fecha_Hora": "📅 Data", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "dash_cols": {"emp": "Empresa", "prod": "Produto", "kg": "Quantidade", "val": "Valor Pago", "com": "Comissão", "mes": "Mês"},
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Massa", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "excel": {"cols": ["Data", "Hora", "Empresa", "Produto", "Kg", "Valor (R$)", "Comissão (R$)"], "total": "TOTAL:", "filename": "Relatorio"},
        "install_guide": "📲 **Como instalar no celular:**\n\n1. No Chrome/Safari, toque em **Compartilhar** o **Menu** (três pontos).\n2. Selecione **'Adicionar à Tela de Início'**.\n3. Pronto! Agora é um App nativo."
    },
    "Español": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nueva Venta", "🛠️ Admin", "📜 Log"],
        "headers": ["Inteligencia de Negocios", "Registrar Venta", "Gestión", "Auditoría"],
        "metrics": ["Facturación Total", "Volumen (Kg)", "Comisión (2%)", "Ticket Medio", "Mejor Cliente"],
        "charts": ["Tendencia (Diaria)", "Mix de Productos", "Ventas por Empresa"],
        "table_title": "Detalle de Ventas",
        "forms": ["Cliente", "Producto", "Kg", "Valor (R$)", "✅ Confirmar Venta"],
        "actions": ["Guardar Edición", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk_label": "Gestión Masiva (Borrar Varios)",
        "clean_hist_label": "Limpieza de Historial",
        "download_label": "📗 Exportar a Excel (.xlsx)",
        "logout_label": "🔒 Cerrar Sesión",
        "goal_label": "🎯 Meta de",
        "goal_save": "💾 Salvar Meta del Mes",
        "goal_text": "Progreso Mensual",
        "msgs": ["¡Venta Registrada!", "¡Borrado con éxito!", "Sin datos", "¡Meta Actualizada!"],
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "col_map": {"Fecha_Hora": "📅 Fecha", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "dash_cols": {"emp": "Empresa", "prod": "Producto", "kg": "Cantidad", "val": "Valor Pagado", "com": "Comisión", "mes": "Mes"},
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Masa", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "excel": {"cols": ["Fecha", "Hora", "Empresa", "Producto", "Kg", "Valor (R$)", "Comisión (R$)"], "total": "TOTAL:", "filename": "Reporte"},
        "install_guide": "📲 **Cómo instalar en el celular:**\n\n1. En Chrome/Safari, toca **Compartir** o el **Menú** (tres puntos).\n2. Selecciona **'Agregar a Pantalla de Inicio'**.\n3. ¡Listo! Ahora es una App nativa."
    },
    "English": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ New Sale", "🛠️ Admin", "📜 Log"],
        "headers": ["Business Intelligence", "Register Sale", "Management", "Audit Log"],
        "metrics": ["Total Revenue", "Volume (Kg)", "Commission (2%)", "Avg. Ticket", "Top Client"],
        "charts": ["Trend (Daily)", "Product Mix", "Sales by Company"],
        "table_title": "Sales Details",
        "forms": ["Client", "Product", "Kg", "Value (R$)", "✅ Confirm Sale"],
        "actions": ["Save Edit", "DELETE", "Search...", "✨ New...", "🗑️ Delete Selection"],
        "bulk_label": "Bulk Management",
        "clean_hist_label": "Clear History",
        "download_label": "📗 Export to Excel (.xlsx)",
        "logout_label": "🔒 Log Out",
        "goal_label": "🎯 Goal for",
        "goal_save": "💾 Save Month Goal",
        "goal_text": "Monthly Progress",
        "msgs": ["Sale Registered!", "Deleted successfully!", "No data", "Goal Updated!"],
        "new_labels": ["Client Name:", "Product Name:"],
        "col_map": {"Fecha_Hora": "📅 Date", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "dash_cols": {"emp": "Company", "prod": "Product", "kg": "Quantity", "val": "Value Paid", "com": "Commission", "mes": "Month"},
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Deleted", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean", "META_UPDATE": "🎯 Goal"},
        "excel": {"cols": ["Date", "Time", "Company", "Product", "Kg", "Value (R$)", "Commission (R$)"], "total": "TOTAL:", "filename": "Report"},
        "install_guide": "📲 **How to install on mobile:**\n\n1. In Chrome/Safari, tap **Share** or **Menu** (three dots).\n2. Select **'Add to Home Screen'**.\n3. Done! It's now a native App."
    }
}

RATES = {
    "Português": {"s": "R$", "r": 1.0},
    "Español":   {"s": "$", "r": 165.0},
    "English":   {"s": "USD", "r": 0.18}
}

# --- CONEXIÓN ---
def get_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    book = client.open("Inventario_Xingu_DB")
    return book

def log_action(book, action, detail):
    try:
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, detail])
    except: pass

# --- FUNCIÓN DE META MEJORADA (LEE POR POSICIÓN, NO POR NOMBRE) ---
def get_monthly_goal_from_db(book, current_period_key):
    try:
        sheet_log = book.worksheet("Historial")
        # Usamos get_all_values para ignorar encabezados rotos
        rows = sheet_log.get_all_values()
        
        # Iteramos de atrás hacia adelante (lo más reciente primero)
        # rows[1:] ignora la fila 0 (headers)
        for row in reversed(rows[1:]): 
            if len(row) >= 3:
                # Columna 1 (B) es Acción, Columna 2 (C) es Detalles
                accion = str(row[1])
                detalle = str(row[2])
                
                if accion == 'META_UPDATE':
                    if "|" in detalle:
                        periodo, valor = detalle.split("|")
                        if periodo == current_period_key:
                            return float(valor)
    except: pass
    return 0.0

# --- APP PRINCIPAL ---
def main():
    if not check_password():
        return

    with st.sidebar:
        st.markdown(f"<h1 style='text-align: center; font-size: 60px; margin-bottom: 0;'>{ICONO_APP}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{NOMBRE_EMPRESA}</h3>", unsafe_allow_html=True)
        
        lang = st.selectbox("Language / Idioma", ["Português", "Español", "English"])
        
        with st.expander("📲 Instalar App"):
            st.info(TR[lang]["install_guide"])

        st.markdown("---")
        st.caption("v38.0 Goal Fixed")
    
    t = TR[lang]
    s = RATES[lang]["s"]
    r = RATES[lang]["r"]

    try:
        book = get_data()
        sheet = book.sheet1
        df = pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error(f"Error DB: {e}")
        st.stop()

    if not df.empty:
        for col in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0
        empresas = sorted(list(set(df['Empresa'].astype(str))))
        prods_db = sorted(list(set(df['Producto'].astype(str))))
    else:
        empresas, prods_db = [], []
    
    productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_db)))

    # --- TIEMPO ---
    ahora = datetime.now()
    mes_ui_dict = MONTHS_UI[lang]
    mes_actual_nombre = mes_ui_dict[ahora.month]
    periodo_clave = ahora.strftime("%Y-%m")

    # --- SIDEBAR: META PERSISTENTE ---
    with st.sidebar:
        st.subheader(f"{t['goal_text']} ({mes_actual_nombre})")
        db_goal = get_monthly_goal_from_db(book, periodo_clave)
        label_dinamico = f"{t['goal_label']} {mes_actual_nombre} ({s})"
        meta_input = st.number_input(label_dinamico, value=db_goal, step=1000.0)
        
        if st.button(t['goal_save'], type="primary"):
            valor_a_guardar = f"{periodo_clave}|{meta_input}"
            log_action(book, "META_UPDATE", valor_a_guardar)
            st.success(t['msgs'][3])
            time.sleep(1)
            st.rerun()

        if not df.empty:
            df['Fecha_DT'] = pd.to_datetime(df['Fecha_Registro'], errors='coerce')
            df_mes_actual = df[df['Fecha_DT'].dt.to_period('M') == periodo_clave]
            val_mes_brl = df_mes_actual['Valor_BRL'].sum()
            val_mes_curr = val_mes_brl * r
            kg_mes = df_mes_actual['Kg'].sum()
        else:
            val_mes_curr = 0
            kg_mes = 0

        if meta_input > 0:
            progreso = min(val_mes_curr / meta_input, 1.0)
            st.progress(progreso)
            porcentaje = (val_mes_curr / meta_input) * 100
            st.caption(f"{porcentaje:.1f}% ({s} {val_mes_curr:,.0f} / {s} {meta_input:,.0f})")
            if progreso >= 1.0: st.balloons()
        else:
            st.warning("Defina a meta.")
        
        st.divider()

        # EXCEL
        if not df.empty:
            buffer = io.BytesIO()
            df_export = df.copy()
            df_export['Fecha_Temp'] = pd.to_datetime(df_export['Fecha_Registro'], errors='coerce')
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                workbook = writer.book
                fmt_header = workbook.add_format({'bold': True, 'fg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                fmt_currency = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
                fmt_number = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
                fmt_base = workbook.add_format({'border': 1})
                fmt_total = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'num_format': 'R$ #,##0.00', 'border': 1})

                df_export['Periodo'] = df_export['Fecha_Temp'].dt.to_period('M')
                for periodo in sorted(df_export['Periodo'].unique(), reverse=True):
                    data_mes = df_export[df_export['Periodo'] == periodo].copy()
                    data_mes['Fecha'] = data_mes['Fecha_Temp'].dt.strftime('%d/%m/%Y')
                    data_mes['Hora'] = data_mes['Fecha_Temp'].dt.strftime('%H:%M')
                    
                    cols_db = ['Fecha', 'Hora', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']
                    data_final = data_mes[[c for c in cols_db if c in data_mes.columns]]
                    
                    nombre_mes_lang = mes_ui_dict[periodo.month]
                    name = f"{nombre_mes_lang} {periodo.year}"
                    
                    data_final.to_excel(writer, sheet_name=name, startrow=1, header=False, index=False)
                    ws = writer.sheets[name]
                    
                    headers_lang = t['excel']['cols']
                    for i, h in enumerate(headers_lang): ws.write(0, i, h, fmt_header)
                    
                    ws.set_column('A:B', 10, fmt_base)
                    ws.set_column('C:D', 22, fmt_base)
                    ws.set_column('E:E', 10, fmt_number)
                    ws.set_column('F:G', 15, fmt_currency)
                    
                    rw = len(data_final)+1
                    ws.write(rw, 4, t['excel']['total'], fmt_total)
                    ws.write(rw, 5, data_final['Valor_BRL'].sum(), fmt_total)
                    ws.write(rw, 6, data_final['Comissao_BRL'].sum(), fmt_total)

            filename_prefix = t['excel']['filename']
            st.download_button(
                label=t['download_label'],
                data=buffer, 
                file_name=f'{filename_prefix}_{NOMBRE_EMPRESA}_{datetime.now().strftime("%Y-%m")}.xlsx', 
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary"
            )
        
        st.write("")
        if st.button(t['logout_label'], type="secondary"):
            st.session_state.password_correct = False
            st.rerun()

    tab_dash, tab_add, tab_admin, tab_log = st.tabs(t['tabs'])

    # 1️⃣ DASHBOARD CEO
    with tab_dash:
        st.title(t['headers'][0])
        if not df.empty:
            val_total = df['Valor_BRL'].sum() * r
            kg_total = df['Kg'].sum()
            com_total = (df['Valor_BRL'].sum() * 0.02) * r
            ticket_medio = val_total / len(df) if len(df) > 0 else 0
            
            top_client_name = "---"
            if not df.empty:
                top_client = df.groupby('Empresa')['Valor_BRL'].sum().idxmax()
                top_client_val = df.groupby('Empresa')['Valor_BRL'].sum().max() * r
                top_client_name = f"{top_client} ({s} {top_client_val:,.0f})"

            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {val_total:,.0f}", delta="Total")
            k2.metric(t['metrics'][1], f"{kg_total:,.0f} kg")
            k3.metric(t['metrics'][2], f"{s} {com_total:,.0f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            k4, k5 = st.columns(2)
            k4.metric(t['metrics'][3], f"{s} {ticket_medio:,.0f}", help="Valor Médio")
            k5.metric(t['metrics'][4], top_client_name, delta="VIP 👑")

            st.divider()

            # --- TABLA PROFESIONAL ---
            st.subheader(t['table_title'])
            
            df_table = df.copy()
            df_table['Val_Show'] = df_table['Valor_BRL'] * r
            df_table['Com_Show'] = (df_table['Valor_BRL'] * 0.02) * r
            df_table['Fecha_DT_Calc'] = pd.to_datetime(df_table['Fecha_Registro'], errors='coerce')
            df_table['Mes_Auto'] = df_table['Fecha_DT_Calc'].dt.month.map(mes_ui_dict)
            
            cols_renombrar = {
                'Mes_Auto': t['dash_cols']['mes'], 
                'Empresa': t['dash_cols']['emp'],
                'Producto': t['dash_cols']['prod'],
                'Kg': t['dash_cols']['kg'],
                'Val_Show': t['dash_cols']['val'],
                'Com_Show': t['dash_cols']['com']
            }
            
            df_table = df_table.rename(columns=cols_renombrar)
            
            cols_final = [
                t['dash_cols']['mes'], 
                t['dash_cols']['emp'], 
                t['dash_cols']['prod'], 
                t['dash_cols']['kg'], 
                t['dash_cols']['val'], 
                t['dash_cols']['com']
            ]
            
            st.dataframe(
                df_table[cols_final].iloc[::-1],
                use_container_width=True,
                hide_index=True,
                column_config={
                    t['dash_cols']['val']: st.column_config.NumberColumn(
                        label=t['dash_cols']['val'],
                        format=f"{s} %.2f"
                    ),
                    t['dash_cols']['com']: st.column_config.NumberColumn(
                        label=t['dash_cols']['com'],
                        format=f"{s} %.2f"
                    ),
                    t['dash_cols']['kg']: st.column_config.NumberColumn(
                        label=t['dash_cols']['kg'],
                        format="%.1f kg"
                    )
                }
            )

            st.divider()

            # --- GRÁFICOS ---
            c_izq, c_der = st.columns([2, 1])
            with c_izq:
                df['Fecha_DT'] = pd.to_datetime(df['Fecha_Registro'], errors='coerce')
                df['Fecha_Dia'] = df['Fecha_DT'].dt.date
                df['Valor_View'] = df['Valor_BRL'] * r
                df_trend = df.groupby('Fecha_Dia')['Valor_View'].sum().reset_index()
                
                st.subheader(t['charts'][0])
                fig_line = px.area(df_trend, x='Fecha_Dia', y='Valor_View', markers=True)
                fig_line.update_layout(xaxis_title="", yaxis_title=s, height=350)
                fig_line.update_traces(line_color='#FF4B4B', fillcolor='rgba(255, 75, 75, 0.2)')
                st.plotly_chart(fig_line, use_container_width=True)

            with c_der:
                st.subheader(t['charts'][1]) 
                fig_pie = px.pie(df, names='Producto', values='Kg', hole=0.6)
                fig_pie.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=350)
                st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.info(t['msgs'][2])

    # 2️⃣ VENDER
    with tab_add:
        st.header(t['headers'][1])
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sel_emp = c1.selectbox(t['forms'][0], [t['actions'][3]] + empresas)
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == t['actions'][3] else sel_emp
            
            sel_prod = c2.selectbox(t['forms'][1], [t['actions'][3]] + productos)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == t['actions'][3] else sel_prod
            
            kg = c1.number_input(t['forms'][2], step=10.0)
            val = c2.number_input(t['forms'][3], step=100.0)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['forms'][4], type="primary"):
                if emp and prod:
                    ahora = datetime.now()
                    mes_db = MESES_PT[ahora.month]
                    row = [emp, prod, kg, val, val*0.02, ahora.strftime("%Y-%m-%d %H:%M:%S"), mes_db]
                    sheet.append_row(row)
                    log_action(book, "NEW", f"{emp} | {kg}kg | {s} {val:,.2f}")
                    st.success(t['msgs'][0])
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()

    # 3️⃣ ADMIN
    with tab_admin:
        st.header(t['headers'][2])
        filtro = st.text_input("🔍 " + t['actions'][2], placeholder="Ej: Julio, Açai...")
        
        if not df.empty:
            df_show = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df.tail(10).iloc[::-1]
            for i, r in df_show.iterrows():
                with st.expander(f"📌 {r['Empresa']} | {r['Producto']} ({r['Fecha_Registro']})"):
                    c1, c2 = st.columns(2)
                    nk = c1.number_input("Kg", value=float(r['Kg']), key=f"k{i}")
                    nv = c2.number_input("R$", value=float(r['Valor_BRL']), key=f"v{i}")
                    if st.button(t['actions'][0], key=f"u{i}"):
                        cel = sheet.find(str(r['Fecha_Registro']))
                        if cel:
                            sheet.update_cell(cel.row, 3, nk)
                            sheet.update_cell(cel.row, 4, nv)
                            sheet.update_cell(cel.row, 5, nv*0.02)
                            log_action(book, "EDITAR", f"{r['Empresa']}")
                            st.success("OK!")
                            time.sleep(1)
                            st.rerun()
            st.divider()
            with st.expander(t['bulk_label']):
                df_rev = df.iloc[::-1].reset_index()
                opc = [f"{r['Empresa']} | {r['Producto']} | {r['Fecha_Registro']}" for i, r in df_rev.iterrows()]
                sels = st.multiselect(t['msgs'][3], opc)
                if st.button(t['actions'][4], type="primary"):
                    if sels:
                        dates = [x.split(" | ")[-1] for x in sels]
                        rows = []
                        all_recs = sheet.get_all_records()
                        for i, r in enumerate(all_recs):
                            if str(r['Fecha_Registro']) in dates: rows.append(i + 2)
                        rows.sort(reverse=True)
                        for rw in rows: sheet.delete_rows(rw)
                        log_action(book, "BORRADO_MASIVO", f"{len(rows)}")
                        st.success(t['msgs'][1])
                        time.sleep(1)
                        st.rerun()

    # 4️⃣ HISTORIAL
    with tab_log:
        st.title(t['headers'][3])
        try:
            sh_log = book.worksheet("Historial")
            h_dt = pd.DataFrame(sh_log.get_all_records())
            if not h_dt.empty:
                show_log = h_dt.copy().rename(columns=t['col_map'])
                show_log[t['col_map']["Accion"]] = show_log[t['col_map']["Accion"]].replace(t['val_map'])
                st.dataframe(show_log.iloc[::-1], use_container_width=True)
                st.divider()
                with st.expander(t['clean_hist_label']):
                    rev_h = h_dt.iloc[::-1].reset_index()
                    opc_h = [f"{r['Fecha_Hora']} | {r['Accion']} | {r['Detalles']}" for i, r in rev_h.iterrows()]
                    sel_h = st.multiselect(t['msgs'][3], opc_h)
                    if st.button(t['actions'][4], key="btn_h", type="primary"):
                        if sel_h:
                            dts_h = [x.split(" | ")[0] for x in sel_h]
                            all_rows = sh_log.get_all_values()
                            dels = []
                            for i, row in enumerate(all_rows):
                                if i==0: continue
                                if row[0] in dts_h: dels.append(i+1)
                            dels.sort(reverse=True)
                            for d in dels: sh_log.delete_rows(d)
                            st.success(t['msgs'][1])
                            time.sleep(1)
                            st.rerun()
        except: st.warning("Falta Hoja Historial")

if __name__ == "__main__":
    main()
