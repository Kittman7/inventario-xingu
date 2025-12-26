import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io
import xlsxwriter

# INTENTO DE IMPORTAR FPDF
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ==========================================
# 🎨 ZONA DE PERSONALIZACIÓN
# ==========================================
NOMBRE_EMPRESA = "Xingu CEO"
ICONO_APP = "🍇"

# 🔑 LOGIN SIMPLE
CONTRASEÑA_MAESTRA = "Julio777" 
# ==========================================

st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetric"] {
        background-color: #1E1E1E; border-radius: 10px; padding: 15px;
        border: 1px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3em; font-weight: 700; border: none; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SIMPLE ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = "CEO" 

    if st.session_state.authenticated:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA}</h1>", unsafe_allow_html=True)
        st.write("")
        with st.form("login_form"):
            input_pass = st.text_input("Senha / Contraseña", type="password")
            submit_btn = st.form_submit_button("Entrar", type="primary")
        
        if submit_btn:
            if input_pass.strip() == CONTRASEÑA_MAESTRA:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("🚫 Incorrecto")
    return False

# --- PDF ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'{NOMBRE_EMPRESA} - Recibo', 0, 1, 'C'); self.ln(5)
    def create_pdf(cli, prod, kg, val, vend):
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Vendedor: {vend}", ln=True)
        pdf.line(10, 35, 200, 35); pdf.ln(10)
        pdf.cell(0, 10, f"Cliente: {cli}", ln=True); pdf.ln(5)
        pdf.cell(100, 10, "Produto", 1); pdf.cell(40, 10, "Kg", 1); pdf.cell(50, 10, "Valor", 1); pdf.ln()
        pdf.cell(100, 10, f"{prod}", 1); pdf.cell(40, 10, f"{kg}", 1); pdf.cell(50, 10, f"R$ {val:,.2f}", 1)
        return pdf.output(dest='S').encode('latin-1')

# --- MAPA DE MESES ---
MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
MONTHS_UI = {
    "Português": MESES_PT,
    "Español": {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"},
    "English": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
}

# --- DICCIONARIO ---
TR = {
    "Português": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nova Venda", "🛠️ Admin (Stock)", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venda", "Gestão de Estoque", "Auditoria"],
        "metrics": ["Faturamento", "Volume Vendido", "Comissão", "Ticket Médio", "Melhor Cliente"],
        "charts": ["Tendência", "Mix Produtos", "Por Empresa"],
        "stock_add_title": "📦 Adicionar Estoque",
        "stock_btn": "➕ Adicionar",
        "stock_alert": "Estoque Atual",
        "table_title": "Detalhes",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar Venda"],
        "actions": ["Salvar", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk_label": "Gestão em Massa (Apagar Vários)",
        "clean_hist_label": "Limpeza de Histórico",
        "dl_excel": "📗 Baixar Relatório (Pro)",
        "logout": "🔒 Sair",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar Meta",
        "new_labels": ["Nome Cliente:", "Nome Produto:"],
        "dash_cols": {"val": "Valor", "com": "Comissão", "kg": "Kg", "emp": "Empresa", "prod": "Produto", "mes": "Mês"},
        "msgs": ["Sucesso!", "Apagado!", "Sem dados", "Atualizado!", "Seleccione items"],
        "stock_msg": "Estoque Adicionado!",
        "install": "📲 Instalar: Menu -> Adicionar à Tela de Início",
        "filter": "📅 Filtrar por Data",
        "xls_head": ["Data", "Mês", "Empresa", "Produto", "Kg", "Valor (R$)", "Comissão (R$)"],
        "xls_tot": "TOTAL GERAL:",
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Massa", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "col_map": {"Fecha_Hora": "📅 Data", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"}
    },
    "Español": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nueva Venta", "🛠️ Admin (Stock)", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venta", "Gestión", "Auditoría"],
        "metrics": ["Facturación", "Volumen Vendido", "Comisión", "Ticket Medio", "Top Cliente"],
        "charts": ["Tendencia", "Mix Productos", "Por Empresa"],
        "stock_add_title": "📦 Añadir Stock",
        "stock_btn": "➕ Sumar",
        "stock_alert": "Stock Actual",
        "table_title": "Detalles",
        "forms": ["Cliente", "Producto", "Kg", "Valor ($)", "✅ Confirmar Venta"],
        "actions": ["Guardar", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk_label": "Gestión Masiva (Borrar Varios)",
        "clean_hist_label": "Limpieza de Historial",
        "dl_excel": "📗 Bajar Reporte (Pro)",
        "logout": "🔒 Salir",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar Meta",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "dash_cols": {"val": "Valor", "com": "Comisión", "kg": "Kg", "emp": "Empresa", "prod": "Producto", "mes": "Mes"},
        "msgs": ["¡Éxito!", "¡Borrado!", "Sin datos", "¡Actualizado!", "Seleccione items"],
        "stock_msg": "¡Stock Añadido!",
        "install": "📲 Instalar: Menú -> Agregar a Pantalla de Inicio",
        "filter": "📅 Filtrar por Fecha",
        "xls_head": ["Fecha", "Mes", "Empresa", "Producto", "Kg", "Valor ($)", "Comisión ($)"],
        "xls_tot": "TOTAL GENERAL:",
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Masa", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "col_map": {"Fecha_Hora": "📅 Fecha", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"}
    },
    "English": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ New Sale", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "New Sale", "Management", "Log"],
        "metrics": ["Revenue", "Volume Sold", "Commission", "Avg Ticket", "Top Client"],
        "charts": ["Trend", "Mix", "By Company"],
        "stock_add_title": "📦 Add Stock",
        "stock_btn": "➕ Add",
        "stock_alert": "Current Stock",
        "table_title": "Details",
        "forms": ["Client", "Product", "Kg", "Value", "✅ Confirm Sale"],
        "actions": ["Save", "DELETE", "Search...", "✨ New...", "🗑️ Delete Selection"],
        "bulk_label": "Bulk Management",
        "clean_hist_label": "Clear History",
        "dl_excel": "📗 Download Report (Pro)",
        "logout": "🔒 Logout",
        "goal_lbl": "🎯 Goal for", "goal_btn": "💾 Save Goal",
        "new_labels": ["Client Name:", "Product Name:"],
        "dash_cols": {"val": "Value", "com": "Comm", "kg": "Kg", "emp": "Company", "prod": "Product", "mes": "Month"},
        "msgs": ["Success!", "Deleted!", "No data", "Updated!", "Select items"],
        "stock_msg": "Stock Added!",
        "install": "📲 Install: Menu -> Add to Home Screen",
        "filter": "📅 Filter by Date",
        "xls_head": ["Date", "Month", "Company", "Product", "Kg", "Value", "Commission"],
        "xls_tot": "GRAND TOTAL:",
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Deleted", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean", "META_UPDATE": "🎯 Goal"},
        "col_map": {"Fecha_Hora": "📅 Date", "Accion": "⚡ Action", "Detalles": "📝 Details"}
    }
}
RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }
MESES_UI_SIDEBAR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# --- DATA ---
@st.cache_resource(ttl=600) 
def get_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    return client

def get_data():
    client = get_connection()
    book = client.open("Inventario_Xingu_DB")
    return book

def log_action(book, action, detail):
    try:
        u = st.session_state.get('username', 'CEO')
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, f"{detail} ({u})"])
    except: pass

def get_goal(book, key):
    try:
        rows = book.worksheet("Historial").get_all_values()
        for row in reversed(rows[1:]):
            if len(row) >= 3 and row[1] == 'META_UPDATE' and "|" in str(row[2]):
                p, v = str(row[2]).split("|")
                if p == key: return float(v)
    except: pass
    return 0.0

# --- APP ---
def main():
    if not check_password(): return

    with st.sidebar:
        st.markdown(f"<h1 style='text-align: center; font-size: 50px; margin:0;'>{ICONO_APP}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{NOMBRE_EMPRESA}</h3>", unsafe_allow_html=True)
        lang = st.selectbox("Idioma", ["Português", "Español", "English"])
        
        t = TR.get(lang, TR["Português"]) 
        st.caption("v55.0 Final Design")
        if st.button(t['logout']): st.session_state.authenticated = False; st.rerun()
    
    s = RATES[lang]["s"]; r = RATES[lang]["r"]

    # --- DATA LOADING (CON PROTECCIÓN MEJORADA) ---
    df_sales = pd.DataFrame()
    df_stock_in = pd.DataFrame()
    book = None
    sheet_sales = None
    sheet_stock = None

    try:
        book = get_data()
        sheet_sales = book.sheet1 # Intenta abrir la hoja 1 por defecto
        df_sales = pd.DataFrame(sheet_sales.get_all_records())
    except: 
        # Si falla, intentamos reconectar o mostrar error amable
        st.error("Error conectando con Google Sheets. Revisa que el archivo 'Inventario_Xingu_DB' exista y tenga la hoja 1.")
        st.stop()

    try:
        sheet_stock = book.worksheet("Estoque")
        df_stock_in = pd.DataFrame(sheet_stock.get_all_records())
    except:
        # No paramos la app si falta stock, solo avisamos
        df_stock_in = pd.DataFrame(columns=["Data", "Produto", "Kg", "Usuario"]) 

    # --- PROCESAMIENTO ---
    # 1. Ventas
    if not df_sales.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df_sales.columns: df_sales[c] = pd.to_numeric(df_sales[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df_sales['Empresa'].astype(str))))
        prods_sales = list(set(df_sales['Producto'].astype(str)))
        
        # Generar Mes y Fecha DT
        df_sales['Fecha_DT'] = pd.to_datetime(df_sales['Fecha_Registro'], errors='coerce')
        df_sales['Mes_Lang'] = df_sales['Fecha_DT'].dt.month.map(MONTHS_UI[lang])
    else: 
        empresas, prods_sales = [], []
        df_sales = pd.DataFrame(columns=['Producto', 'Kg', 'Valor_BRL', 'Fecha_Registro', 'Empresa', 'Comissao_BRL'])

    # 2. Stock
    if not df_stock_in.empty:
        df_stock_in['Kg'] = pd.to_numeric(df_stock_in['Kg'], errors='coerce').fillna(0)
        prods_stock = list(set(df_stock_in['Produto'].astype(str)))
    else:
        prods_stock = []

    productos_all = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_sales + prods_stock)))

    # 3. Calculo Stock
    stock_real = {}
    for p in productos_all:
        total_in = df_stock_in[df_stock_in['Produto'] == p]['Kg'].sum() if not df_stock_in.empty else 0
        total_out = df_sales[df_sales['Producto'] == p]['Kg'].sum() if not df_sales.empty else 0
        stock_real[p] = total_in - total_out

    # --- SIDEBAR: META & EXCEL ---
    ahora = datetime.now(); periodo_clave = ahora.strftime("%Y-%m")
    with st.sidebar:
        st.write(f"**{t['goal_lbl']} {MESES_UI_SIDEBAR[ahora.month]}**")
        db_goal = get_goal(book, periodo_clave)
        meta = st.number_input("Meta", value=db_goal, step=1000.0, label_visibility="collapsed")
        if st.button(t['goal_btn']):
            log_action(book, "META_UPDATE", f"{periodo_clave}|{meta}")
            st.success("OK!"); time.sleep(1); st.rerun()
        
        val_mes = df_sales[df_sales['Fecha_Registro'].str.contains(periodo_clave, na=False)]['Valor_BRL'].sum() * r if not df_sales.empty else 0
        if meta > 0:
            st.progress(min(val_mes/meta, 1.0))
            st.caption(f"{val_mes/meta*100:.1f}% ({s} {val_mes:,.0f} / {s} {meta:,.0f})")
        st.divider()
        
        if not df_sales.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_ex = df_sales.copy()
                df_ex['Fecha_Clean'] = df_ex['Fecha_DT'].dt.strftime('%d/%m/%Y %H:%M')
                
                data_final = df_ex[['Fecha_Clean', 'Mes_Lang', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']].copy()
                sheet_name = 'Reporte'
                data_final.to_excel(writer, index=False, sheet_name=sheet_name, startrow=1, header=False)
                
                workbook = writer.book
                ws = writer.sheets[sheet_name]
                fmt_head = workbook.add_format({'bold': True, 'fg_color': '#2C3E50', 'font_color': 'white', 'border': 1, 'align': 'center'})
                fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
                fmt_num = workbook.add_format({'num_format': '0.0', 'border': 1, 'align': 'center'})
                fmt_base = workbook.add_format({'border': 1})
                fmt_total = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'num_format': 'R$ #,##0.00', 'border': 1})
                
                for col_num, h in enumerate(t['xls_head']): ws.write(0, col_num, h, fmt_head)
                ws.set_column('A:A', 18, fmt_base); ws.set_column('B:B', 12, fmt_base); ws.set_column('C:D', 22, fmt_base)
                ws.set_column('E:E', 12, fmt_num); ws.set_column('F:G', 18, fmt_money)
                
                lr = len(data_final) + 1
                ws.write(lr, 3, t['xls_tot'], fmt_total)
                ws.write(lr, 4, data_final['Kg'].sum(), fmt_total)
                ws.write(lr, 5, data_final['Valor_BRL'].sum(), fmt_total)
                ws.write(lr, 6, data_final['Comissao_BRL'].sum(), fmt_total)

            st.download_button(t['dl_excel'], data=buffer, file_name=f"Reporte_{datetime.now().strftime('%Y-%m-%d')}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    tab1, tab2, tab3, tab4 = st.tabs(t['tabs'])

    # 1. DASHBOARD (ORDEN CAMBIADO)
    with tab1:
        st.title(t['headers'][0])
        if not df_sales.empty:
            with st.expander(t.get("filter", "Filter Date"), expanded=False):
                col_f1, col_f2 = st.columns(2)
                d_min = df_sales['Fecha_DT'].min().date()
                d_max = df_sales['Fecha_DT'].max().date()
                d1 = col_f1.date_input("Start", d_min)
                d2 = col_f2.date_input("End", d_max)
            
            mask = (df_sales['Fecha_DT'].dt.date >= d1) & (df_sales['Fecha_DT'].dt.date <= d2)
            df_fil = df_sales.loc[mask]

            if df_fil.empty: st.warning("No Data in Range")
            else:
                k1, k2, k3 = st.columns(3)
                k1.metric(t['metrics'][0], f"{s} {(df_fil['Valor_BRL'].sum() * r):,.0f}")
                k2.metric(t['metrics'][1], f"{df_fil['Kg'].sum():,.0f} kg")
                k3.metric(t['metrics'][2], f"{s} {(df_fil['Valor_BRL'].sum()*0.02*r):,.0f}")
                
                st.divider()
                st.subheader(t['stock_alert'])
                if stock_real:
                    for p, kg_left in sorted(stock_real.items(), key=lambda item: item[1], reverse=True):
                        if kg_left != 0 or p in prods_stock or p in prods_sales:
                            c_s1, c_s2 = st.columns([3, 1])
                            pct = max(0.0, min(kg_left / 1000.0, 1.0))
                            c_s1.progress(pct, text=f"📦 **{p}**: {kg_left:,.1f} kg")
                            if kg_left < 0: c_s2.error(f"⚠️ ({kg_left})")
                            elif kg_left < 50: c_s2.warning("⚠️")
                            else: c_s2.success("✅")
                
                st.divider()

                # --- TABLA DETALLES (ARRIBA) ---
                st.subheader(t['table_title'])
                
                # Preparamos tabla visual (Con Mes y Comisión)
                df_show = df_fil[['Fecha_Registro', 'Mes_Lang', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']].copy()
                
                # Renombrar para visualización
                cols_view = {
                    'Fecha_Registro': t['col_map']['Fecha_Hora'],
                    'Mes_Lang': t['dash_cols']['mes'],
                    'Empresa': t['dash_cols']['emp'],
                    'Producto': t['dash_cols']['prod'],
                    'Kg': t['dash_cols']['kg'],
                    'Valor_BRL': t['dash_cols']['val'],
                    'Comissao_BRL': t['dash_cols']['com']
                }
                
                st.dataframe(
                    df_show.rename(columns=cols_view).iloc[::-1],
                    use_container_width=True, hide_index=True,
                    column_config={
                        t['dash_cols']['val']: st.column_config.NumberColumn(format=f"{s} %.2f"),
                        t['dash_cols']['com']: st.column_config.NumberColumn(format=f"{s} %.2f"),
                        t['dash_cols']['kg']: st.column_config.NumberColumn(format="%.1f kg")
                    }
                )
                
                st.divider()
                
                # GRÁFICOS (ABAJO)
                c_izq, c_der = st.columns([2, 1])
                with c_izq:
                    df_tr = df_fil.groupby(df_fil['Fecha_DT'].dt.date)['Valor_BRL'].sum().reset_index()
                    df_tr.columns = ['Fecha', 'Venta']
                    df_tr['Venta'] = df_tr['Venta'] * r
                    fig = px.line(df_tr, x='Fecha', y='Venta', markers=True, title=t['charts'][0])
                    fig.update_traces(line_color='#FF4B4B')
                    st.plotly_chart(fig, use_container_width=True)
                with c_der:
                    fig2 = px.pie(df_fil, names='Producto', values='Kg', hole=0.5, title=t['charts'][1])
                    fig2.update_layout(showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)

    # 2. VENDER
    with tab2:
        st.header(t['headers'][1])
        with st.container(border=True):
            c1, c2 = st.columns(2)
            op_new = t['actions'][3]
            sel_emp = c1.selectbox(t['forms'][0], [op_new] + empresas)
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == op_new else sel_emp
            sel_prod = c2.selectbox(t['forms'][1], [op_new] + productos_all)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == op_new else sel_prod
            kg = c1.number_input(t['forms'][2], step=10.0)
            val = c2.number_input(t['forms'][3], step=100.0)
            
            if prod in stock_real: st.caption(f"Stock: {stock_real[prod]:.1f} kg")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['forms'][4], type="primary"):
                if emp and prod:
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto"]
                    sheet_sales.append_row(row)
                    log_action(book, "VENTA", f"{emp} | {kg}kg | {prod}")
                    st.success(t['msgs'][0])
                    if PDF_AVAILABLE:
                        try:
                            pdf_data = create_pdf(emp, prod, kg, val, st.session_state.username)
                            st.download_button(t['pdf'], data=pdf_data, file_name=f"Recibo.pdf", mime="application/pdf")
                        except: pass
                    time.sleep(2); st.rerun()

    # 3. ADMIN (TABLA VISUAL + EDITAR)
    with tab3:
        st.header(t['stock_add_title'])
        with st.container(border=True):
            c_st1, c_st2, c_st3 = st.columns([2, 1, 1])
            prod_stock = c_st1.selectbox("Produto", ["✨ Novo..."] + productos_all, key="stock_prod")
            if prod_stock == "✨ Novo...": prod_stock = c_st1.text_input("Nome", key="stock_prod_new")
            kg_stock = c_st2.number_input("Kg (+)", step=10.0, key="stock_kg")
            if c_st3.button(t['stock_btn'], type="primary"):
                if prod_stock and kg_stock > 0 and sheet_stock:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet_stock.append_row([now, prod_stock, kg_stock, st.session_state.username])
                    log_action(book, "STOCK_ADD", f"{prod_stock} | +{kg_stock}kg")
                    st.success(t['stock_msg']); time.sleep(1.5); st.rerun()
                elif not sheet_stock:
                    st.error("Error: Hoja 'Estoque' no creada en Google Sheets.")

        st.divider()
        st.subheader("Admin Ventas")
        filtro = st.text_input(t['actions'][2], key="admin_search") 
        
        if not df_sales.empty:
            # 1. TABLA GENERAL (COMO HISTORIAL)
            st.caption("Vista General:")
            
            # Preparamos tabla visual para Admin
            df_admin_show = df_sales[['Fecha_Registro', 'Empresa', 'Producto', 'Kg', 'Valor_BRL']].copy()
            # Renombramos para que se vea bonito
            cols_admin = {
                'Fecha_Registro': t['col_map']['Fecha_Hora'],
                'Empresa': t['dash_cols']['emp'],
                'Producto': t['dash_cols']['prod'],
                'Kg': t['dash_cols']['kg'],
                'Valor_BRL': t['dash_cols']['val']
            }
            
            st.dataframe(
                df_admin_show.rename(columns=cols_admin).iloc[::-1], 
                use_container_width=True, hide_index=True,
                column_config={
                    t['dash_cols']['val']: st.column_config.NumberColumn(format=f"{s} %.2f"),
                    t['dash_cols']['kg']: st.column_config.NumberColumn(format="%.1f kg")
                }
            )
            
            st.markdown("---")
            st.caption("🛠️ Editar / Borrar (Individual):")
            
            # 2. EDICIÓN INDIVIDUAL
            df_s = df_sales[df_sales.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df_sales.tail(10).iloc[::-1]
            for i, r in df_s.iterrows():
                with st.expander(f"{r['Empresa']} | {r['Producto']} | {r['Fecha_Registro']}"):
                    c_ed1, c_ed2 = st.columns(2)
                    new_kg = c_ed1.number_input("Kg", value=float(r['Kg']), key=f"k_{i}")
                    new_val = c_ed2.number_input("Valor", value=float(r['Valor_BRL']), key=f"v_{i}")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("💾 Guardar", key=f"save_{i}"):
                        cell = sheet_sales.find(str(r['Fecha_Registro']))
                        sheet_sales.update_cell(cell.row, 3, new_kg)
                        sheet_sales.update_cell(cell.row, 4, new_val)
                        sheet_sales.update_cell(cell.row, 5, new_val*0.02)
                        st.success("Editado!"); time.sleep(1); st.rerun()
                        
                    if c_btn2.button(t['actions'][1], key=f"del_{i}", type="secondary"):
                        cell = sheet_sales.find(str(r['Fecha_Registro']))
                        sheet_sales.delete_rows(cell.row)
                        st.success(t['msgs'][1]); time.sleep(1); st.rerun()
            
            st.divider()
            
            # 3. BORRADO MASIVO
            with st.expander(t['bulk_label']):
                df_rev = df_sales.iloc[::-1].reset_index()
                opc = [f"{r['Empresa']} | {r['Producto']} | {r['Fecha_Registro']}" for i, r in df_rev.iterrows()]
                sels = st.multiselect(t['msgs'][4], opc)
                if st.button(t['actions'][4], type="primary"):
                    if sels:
                        dates = [x.split(" | ")[-1] for x in sels]
                        rows_to_del = []
                        all_recs = sheet_sales.get_all_records()
                        for i, r in enumerate(all_recs):
                            if str(r['Fecha_Registro']) in dates: rows_to_del.append(i + 2)
                        rows_to_del.sort(reverse=True)
                        for rw in rows_to_del: sheet_sales.delete_rows(rw)
                        log_action(book, "BORRADO_MASIVO", f"{len(rows_to_del)}")
                        st.success(t['msgs'][1]); time.sleep(1); st.rerun()

    # 4. LOG
    with tab4:
        st.title(t['headers'][3])
        try:
            sh_log = book.worksheet("Historial")
            h_dt = pd.DataFrame(sh_log.get_all_records())
            if not h_dt.empty:
                show_log = h_dt.copy()
                if "Accion" in show_log.columns:
                    emoji_map = t['val_map'].copy()
                    show_log["Accion"] = show_log["Accion"].replace(emoji_map)
                show_log = show_log.rename(columns=t['col_map'])
                st.dataframe(show_log.iloc[::-1], use_container_width=True)
                
                st.divider()
                with st.expander(t['clean_hist_label']):
                    rev_h = h_dt.iloc[::-1].reset_index()
                    opc_h = [f"{r['Fecha_Hora']} | {r['Accion']} | {r['Detalles']}" for i, r in rev_h.iterrows()]
                    sel_h = st.multiselect(t['msgs'][4], opc_h)
                    if st.button(t['actions'][4], key="btn_h", type="primary"):
                        if sel_h:
                            dts_h = [x.split(" | ")[0] for x in sel_h]
                            all_vals = sh_log.get_all_values()
                            dels = []
                            for i, row in enumerate(all_vals):
                                if i==0: continue
                                if row[0] in dts_h: dels.append(i+1)
                            dels.sort(reverse=True)
                            for d in dels: sh_log.delete_rows(d)
                            st.success(t['msgs'][1]); time.sleep(1); st.rerun()
        except: st.write("Log vacío")

if __name__ == "__main__":
    main()
