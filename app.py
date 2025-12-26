import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io
import xlsxwriter
from PIL import Image
import base64

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
ICONO_ARCHIVO = "logo.png"

# INTENTO DE LEER SECRETS, SINO USA LA FIJA
try:
    CONTRASEÑA_MAESTRA = st.secrets["PASSWORD"]
    USING_SECRETS = True
except:
    CONTRASEÑA_MAESTRA = "Julio777" 
    USING_SECRETS = False
# ==========================================

# --- CONFIGURACIÓN BÁSICA ---
try:
    img_icon = Image.open(ICONO_ARCHIVO)
    st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=img_icon, layout="wide", initial_sidebar_state="collapsed")
except:
    st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon="🍇", layout="wide", initial_sidebar_state="collapsed")

# --- 🚀 FUERZA BRUTA PARA EL ICONO DEL CELULAR ---
def inject_mobile_icon():
    try:
        with open(ICONO_ARCHIVO, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            </style>
            <script>
                var link = document.querySelector("link[rel~='icon']");
                if (!link) {{
                    link = document.createElement('link');
                    link.rel = 'icon';
                    document.getElementsByTagName('head')[0].appendChild(link);
                }}
                link.href = 'data:image/png;base64,{encoded_string}';
            </script>
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{encoded_string}">
                <link rel="shortcut icon" href="data:image/png;base64,{encoded_string}">
            </head>
            """,
            unsafe_allow_html=True
        )
    except: pass

inject_mobile_icon()

# --- ESTILOS CSS OPTIMIZADOS PARA MÓVIL ---
st.markdown("""
    <style>
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Métricas estilo tarjeta */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Botones grandes para dedos (Touch targets) */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em; /* Más alto para tocar fácil */
        font-weight: 600;
        font-size: 16px;
        border: none;
        transition: 0.2s;
    }
    .stButton>button:hover { transform: scale(1.01); }
    
    /* Ajustes para móviles */
    @media only screen and (max-width: 600px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.2rem !important; }
        
        /* Forzar que las pestañas se vean completas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #0E1117;
            border-radius: 5px;
            margin-right: 2px;
            font-size: 12px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'sale_key' not in st.session_state: st.session_state.sale_key = 0
if 'stock_key' not in st.session_state: st.session_state.stock_key = 0
if 'show_log' not in st.session_state: st.session_state.show_log = False
if 'log_filter_override' not in st.session_state: st.session_state.log_filter_override = ""

# --- LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = "CEO" 

    if st.session_state.authenticated:
        return True
    
    c1, c2, c3 = st.columns([1,4,1]) # Más ancho en el medio para móvil
    with c2:
        st.write("")
        st.write("")
        try: st.image(ICONO_ARCHIVO, use_container_width=True)
        except: st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA}</h1>", unsafe_allow_html=True)
        st.write("")
        if not USING_SECRETS:
            st.caption("⚠️ Modo Demo")
        with st.form("login_form"):
            input_pass = st.text_input("Senha / Contraseña", type="password")
            submit_btn = st.form_submit_button("Entrar / Login", type="primary", use_container_width=True)
        if submit_btn:
            if input_pass.strip() == CONTRASEÑA_MAESTRA:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("🚫 Incorrecto")
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

# --- TRADUCCIONES COMPLETAS ---
MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
MONTHS_UI = {
    "Português": MESES_PT,
    "Español": {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"},
    "English": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
}

TR = {
    "Português": {
        "tabs": [f"📊 Dash", "➕ Venda", "📦 Stock", "💰 Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venda", "Gestão de Estoque", "Auditoria"],
        "metrics": ["Faturamento", "Volume", "Comissão", "Ticket Médio", "Melhor Cliente"],
        "charts": ["Tendência", "Mix Produtos", "Por Empresa"],
        "stock_add_title": "📦 Entrada de Estoque",
        "stock_btn": "➕ Adicionar",
        "stock_alert": "Monitoramento",
        "table_title": "Detalhes",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar"],
        "actions": ["Salvar", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk_label": "Gestão em Massa",
        "clean_hist_label": "Limpeza",
        "dl_excel": "📗 Relatório (Excel)",
        "logout": "🔒 Sair",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar",
        "new_labels": ["Nome Cliente:", "Nome Produto:"],
        "dash_cols": {"val": "Valor", "com": "Comissão", "kg": "Kg", "emp": "Empresa", "prod": "Produto", "mes": "Mês"},
        "msgs": ["Sucesso!", "Apagado!", "Sem dados", "Atualizado!", "Selecione items"],
        "stock_msg": "Adicionado!",
        "user_lbl": "Usuário",
        "filter_viz": "👁️ Ver apenas:",
        "save_view": "💾 Salvar Vista",
        "hist_entries": "Histórico de Entradas",
        "search_stk": "🔍 Buscar:",
        "edit_del_stk": "Editar ou Apagar Entrada",
        "save_changes": "💾 Salvar",
        "del_entry": "🗑️ Apagar",
        "wipe_stk_title": "🔥 Apagar TUDO (Perigo)",
        "wipe_stk_warn": "Isso apagará todas as entradas. Irreversível.",
        "wipe_stk_check": "Tenho certeza",
        "wipe_stk_btn": "ZERAR ESTOQUE",
        "admin_sales_title": "💰 Admin Vendas",
        "search_sales": "🔍 Buscar vendas...",
        "wipe_sales_title": "🔥 Apagar TODAS Vendas (Perigo)",
        "wipe_sales_btn": "ZERAR VENDAS",
        "col_map": {"Fecha_Hora": "📅 Data", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "xls_head": ["Data", "Mês", "Empresa", "Produto", "Kg", "Valor (R$)", "Comissão (R$)"],
        "xls_tot": "TOTAL GERAL:",
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Massa", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta", "EDIT_TABLE_STOCK": "✏️ Tbl Stock", "EDIT_TABLE_SALES": "✏️ Tbl Vendas"},
        "alerts": {
            "stock_out": "Esgotado",
            "stock_low": "Baixo",
            "stock_ok": "Disponível",
            "err_stock": "Erro: Estoque insuficiente. Tem",
            "try_sell": "kg e tenta vender",
            "saving": "Salvando...",
            "sold_ok": "Venda registrada!",
            "adding": "Adicionando...",
            "deleting": "Apagando...",
            "wiping": "Excluindo TUDO...",
            "updating": "Atualizando...",
            "backup_title": "🛡️ Backup",
            "backup_desc": "Baixe cópia completa do banco de dados.",
            "backup_btn": "📦 Baixar Backup",
            "backup_load": "Gerando arquivo...",
            "last_sales": "📋 Últimas (Top 3):",
            "tot_sold": "Vendido",
            "excel_edit_mode": "📝 Edição Rápida (Excel)",
            "save_table": "💾 Salvar Tabela",
            "show_all": "👁️ Ver Tudo",
            "lazy_msg": "Mostrando últimas 50.",
            "manual_mode": "📝 Editar Individualmente"
        }
    },
    "Español": {
        "tabs": [f"📊 Dash", "➕ Venta", "📦 Stock", "💰 Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venta", "Gestión", "Auditoría"],
        "metrics": ["Facturación", "Volumen", "Comisión", "Ticket Medio", "Top Cliente"],
        "charts": ["Tendencia", "Mix", "Top Empresas"],
        "stock_add_title": "📦 Entrada Stock",
        "stock_btn": "➕ Sumar",
        "stock_alert": "Monitor",
        "table_title": "Detalles",
        "forms": ["Cliente", "Producto", "Kg", "Valor ($)", "✅ Confirmar"],
        "actions": ["Guardar", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk_label": "Gestión Masiva",
        "clean_hist_label": "Limpieza",
        "dl_excel": "📗 Reporte (Excel)",
        "logout": "🔒 Salir",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "dash_cols": {"val": "Valor", "com": "Comisión", "kg": "Kg", "emp": "Empresa", "prod": "Producto", "mes": "Mes"},
        "msgs": ["¡Éxito!", "¡Borrado!", "Sin datos", "¡Actualizado!", "Seleccione items"],
        "stock_msg": "¡Añadido!",
        "user_lbl": "Usuario",
        "filter_viz": "👁️ Ver solo:",
        "save_view": "💾 Guardar Vista",
        "hist_entries": "Historial Entradas",
        "search_stk": "🔍 Buscar:",
        "edit_del_stk": "Editar o Borrar Entrada",
        "save_changes": "💾 Guardar",
        "del_entry": "🗑️ Borrar",
        "wipe_stk_title": "🔥 Borrar TODO (Peligro)",
        "wipe_stk_warn": "Irreversible.",
        "wipe_stk_check": "Estoy seguro",
        "wipe_stk_btn": "BORRAR TODO STOCK",
        "admin_sales_title": "💰 Admin Ventas",
        "search_sales": "🔍 Buscar...",
        "wipe_sales_title": "🔥 Borrar TODAS Ventas (Peligro)",
        "wipe_sales_btn": "BORRAR TODAS",
        "col_map": {"Fecha_Hora": "📅 Fecha", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "xls_head": ["Fecha", "Mes", "Empresa", "Producto", "Kg", "Valor ($)", "Comisión ($)"],
        "xls_tot": "TOTAL:",
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Masa", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta", "EDIT_TABLE_STOCK": "✏️ Tbl Stock", "EDIT_TABLE_SALES": "✏️ Tbl Ventas"},
        "alerts": {
            "stock_out": "Agotado",
            "stock_low": "Bajo",
            "stock_ok": "Disponible",
            "err_stock": "Error: Insuficiente. Tienes",
            "try_sell": "kg e intentas vender",
            "saving": "Guardando...",
            "sold_ok": "¡Venta registrada!",
            "adding": "Sumando...",
            "deleting": "Borrando...",
            "wiping": "Eliminando TODO...",
            "updating": "Actualizando...",
            "backup_title": "🛡️ Backup",
            "backup_desc": "Descarga copia completa.",
            "backup_btn": "📦 Bajar Backup",
            "backup_load": "Generando...",
            "last_sales": "📋 Últimas (Top 3):",
            "tot_sold": "Vendido",
            "excel_edit_mode": "📝 Edición Rápida (Excel)",
            "save_table": "💾 Guardar Tabla",
            "show_all": "👁️ Ver Todo",
            "lazy_msg": "Mostrando últimas 50.",
            "manual_mode": "📝 Editar Individualmente"
        }
    },
    "English": {
        "tabs": [f"📊 Dash", "➕ Sale", "📦 Stock", "💰 Admin", "📜 Log"],
        "headers": ["Dashboard", "New Sale", "Stock Mgmt", "Log"],
        "metrics": ["Revenue", "Volume", "Commission", "Avg Ticket", "Top Client"],
        "charts": ["Trend", "Mix", "Top Companies"],
        "stock_add_title": "📦 Add Stock",
        "stock_btn": "➕ Add",
        "stock_alert": "Monitor",
        "table_title": "Details",
        "forms": ["Client", "Product", "Kg", "Value", "✅ Confirm"],
        "actions": ["Save", "DELETE", "Search...", "✨ New...", "🗑️ Delete"],
        "bulk_label": "Bulk Mgmt",
        "clean_hist_label": "Clean",
        "dl_excel": "📗 Report",
        "logout": "🔒 Logout",
        "goal_lbl": "🎯 Goal", "goal_btn": "💾 Save",
        "new_labels": ["Client Name:", "Product Name:"],
        "dash_cols": {"val": "Value", "com": "Comm", "kg": "Kg", "emp": "Company", "prod": "Product", "mes": "Month"},
        "msgs": ["Success!", "Deleted!", "No data", "Updated!", "Select items"],
        "stock_msg": "Added!",
        "user_lbl": "User",
        "filter_viz": "👁️ View only:",
        "save_view": "💾 Save View",
        "hist_entries": "Inputs History",
        "search_stk": "🔍 Search:",
        "edit_del_stk": "Edit/Delete Entry",
        "save_changes": "💾 Save",
        "del_entry": "🗑️ Delete",
        "wipe_stk_title": "🔥 Wipe ALL (Danger)",
        "wipe_stk_warn": "Irreversible.",
        "wipe_stk_check": "I am sure",
        "wipe_stk_btn": "WIPE STOCK",
        "admin_sales_title": "💰 Sales Admin",
        "search_sales": "🔍 Search...",
        "wipe_sales_title": "🔥 Wipe ALL Sales (Danger)",
        "wipe_sales_btn": "WIPE SALES",
        "col_map": {"Fecha_Hora": "📅 Date", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "xls_head": ["Date", "Month", "Company", "Product", "Kg", "Value", "Commission"],
        "xls_tot": "TOTAL:",
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "STOCK_ADD": "📦 Stock", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean", "META_UPDATE": "🎯 Goal", "EDIT_TABLE_STOCK": "✏️ Tbl Stock", "EDIT_TABLE_SALES": "✏️ Tbl Sales"},
        "alerts": {
            "stock_out": "Out of Stock",
            "stock_low": "Low Stock",
            "stock_ok": "Available",
            "err_stock": "Error: Insufficient. You have",
            "try_sell": "kg and try to sell",
            "saving": "Saving...",
            "sold_ok": "Registered!",
            "adding": "Adding...",
            "deleting": "Deleting...",
            "wiping": "Wiping ALL...",
            "updating": "Updating...",
            "backup_title": "🛡️ Backup",
            "backup_desc": "Download full copy.",
            "backup_btn": "📦 Download",
            "backup_load": "Generating...",
            "last_sales": "📋 Latest (Top 3):",
            "tot_sold": "Sold",
            "excel_edit_mode": "📝 Quick Edit (Excel)",
            "save_table": "💾 Save Table",
            "show_all": "👁️ Show All",
            "lazy_msg": "Showing last 50.",
            "manual_mode": "📝 Edit Individually"
        }
    }
}
RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }
MESES_UI_SIDEBAR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# --- CONEXIÓN ---
@st.cache_resource(ttl=3600) 
def get_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    return client

@st.cache_data(ttl=900)
def load_cached_data():
    client = get_connection()
    try:
        book = client.open("Inventario_Xingu_DB")
        sheet_sales = book.get_worksheet(0)
        df_sales = pd.DataFrame(sheet_sales.get_all_records())
        try:
            sheet_stock = book.worksheet("Estoque")
            df_stock = pd.DataFrame(sheet_stock.get_all_records())
        except:
            df_stock = pd.DataFrame(columns=["Data", "Produto", "Kg", "Usuario"])
        return df_sales, df_stock
    except Exception as e:
        return None, None

def get_book_direct():
    client = get_connection()
    return client.open("Inventario_Xingu_DB")

def safe_api_action(action_func, *args):
    last_error = None
    for attempt in range(1, 4): 
        try:
            action_func(*args)
            return True, None 
        except Exception as e:
            last_error = e
            time.sleep(2 ** attempt) 
    return False, last_error

def log_action(book, action, detail):
    try:
        u = st.session_state.get('username', 'CEO')
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, f"{detail} ({u})"])
    except: pass

def get_config(book):
    try:
        sh = book.worksheet("Config")
    except:
        sh = book.add_worksheet("Config", 100, 2)
        sh.append_row(["Key", "Value"])
    records = sh.get_all_values()
    cfg = {}
    for r in records[1:]:
        if len(r) >= 2: cfg[r[0]] = r[1]
    return sh, cfg

def save_conf(book, key, val):
    sh, cfg = get_config(book)
    try:
        cell = sh.find(key)
        sh.update_cell(cell.row, 2, str(val))
    except:
        sh.append_row([key, str(val)])

def find_row_by_date(sheet, date_str):
    clean_date = str(date_str).strip()
    try:
        return sheet.find(clean_date)
    except:
        try:
            col_values = sheet.col_values(1)
            for idx, val in enumerate(col_values):
                if str(val).strip() == clean_date:
                    class MockCell:
                        def __init__(self, r): self.row = r
                    return MockCell(idx + 1)
        except: pass
    return None

# ==========================================
# 🧩 FRAGMENTOS
# ==========================================

@st.fragment
def render_dashboard(t, df_sales, stock_real, sales_real, prods_stock, prods_sales, s, r, lang, saved_filter):
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

        if df_fil.empty: st.warning(t['msgs'][2])
        else:
            total_val = df_fil['Valor_BRL'].sum() * r
            total_kg = df_fil['Kg'].sum()
            total_com = total_val * 0.02
            
            # Métricas en columnas que se apilan solas en móvil
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {total_val:,.0f}", delta=None) 
            k2.metric(t['metrics'][1], f"{total_kg:,.0f} kg", delta=None) 
            k3.metric(t['metrics'][2], f"{s} {total_com:,.0f}", delta=None) 
            
            st.divider()
            
            st.subheader(t['stock_alert'])
            all_prods_display = sorted(list(stock_real.keys()))
            
            default_selection = []
            if saved_filter:
                default_selection = [p for p in saved_filter.split(',') if p in all_prods_display]

            with st.expander(t['filter_viz']):
                selected_view = st.multiselect("Select", all_prods_display, default=default_selection, label_visibility="collapsed")
                if st.button(t['save_view'], use_container_width=True):
                    bk = get_book_direct()
                    val_to_save = ",".join(selected_view)
                    save_conf(bk, "stock_view_pref", val_to_save)
                    st.toast(f"✅ {t['msgs'][3]}", icon="💾")
            
            if stock_real:
                items_to_show = {k: v for k, v in stock_real.items() if k in selected_view} if selected_view else stock_real
                for p, kg_left in sorted(items_to_show.items(), key=lambda item: item[1], reverse=True):
                    show_it = False
                    if selected_view: show_it = True 
                    elif kg_left != 0 or p in prods_stock: show_it = True
                    
                    if show_it:
                        kg_sold_total = sales_real.get(p, 0.0)
                        # Barra de progreso optimizada
                        st.write(f"📦 **{p}**")
                        c_s1, c_s2 = st.columns([3, 1])
                        pct = max(0.0, min(kg_left / 1000.0, 1.0))
                        c_s1.progress(pct)
                        c_s2.caption(f"{kg_left:,.1f}kg / 📉 {t['alerts']['tot_sold']}: {kg_sold_total:,.1f}")
            
            st.divider()
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                df_tr = df_fil.groupby(df_fil['Fecha_DT'].dt.date)['Valor_BRL'].sum().reset_index()
                df_tr.columns = ['Fecha', 'Venta']
                df_tr['Venta'] = df_tr['Venta'] * r
                fig_area = px.area(df_tr, x='Fecha', y='Venta', title=t['charts'][0], markers=True)
                fig_area.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis_showgrid=False, margin=dict(l=20, r=20, t=40, b=20))
                fig_area.update_traces(line_color='#FF4B4B', fillcolor='rgba(255, 75, 75, 0.2)')
                st.plotly_chart(fig_area, use_container_width=True)
            with c_chart2:
                fig_donut = px.pie(df_fil, names='Producto', values='Kg', hole=0.6, title=t['charts'][1])
                fig_donut.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_donut, use_container_width=True)

            st.subheader(t['table_title'])
            df_show = df_fil[['Fecha_Registro', 'Mes_Lang', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']].copy()
            cols_view = {'Fecha_Registro': t['col_map']['Fecha_Hora'], 'Mes_Lang': t['dash_cols']['mes'], 'Empresa': t['dash_cols']['emp'], 'Producto': t['dash_cols']['prod'], 'Kg': t['dash_cols']['kg'], 'Valor_BRL': t['dash_cols']['val'], 'Comissao_BRL': t['dash_cols']['com']}
            st.dataframe(df_show.rename(columns=cols_view).iloc[::-1], use_container_width=True, hide_index=True, column_config={t['dash_cols']['val']: st.column_config.NumberColumn(format=f"{s} %.2f"), t['dash_cols']['com']: st.column_config.NumberColumn(format=f"{s} %.2f"), t['dash_cols']['kg']: st.column_config.NumberColumn(format="%.1f kg")})

@st.fragment
def render_new_sale(t, empresas, productos_all, stock_real, df_sales, s):
    st.header(t['headers'][1])
    key_suffix = str(st.session_state.sale_key)
    with st.container(border=True):
        # Campos full width en movil
        sel_emp = st.selectbox(t['forms'][0], [t['actions'][3]] + empresas, key=f"emp_{key_suffix}")
        emp = st.text_input(t['new_labels'][0], key=f"emp_txt_{key_suffix}") if sel_emp == t['actions'][3] else sel_emp
        
        sel_prod = st.selectbox(t['forms'][1], [t['actions'][3]] + productos_all, key=f"prod_{key_suffix}")
        prod = st.text_input(t['new_labels'][1], key=f"prod_txt_{key_suffix}") if sel_prod == t['actions'][3] else sel_prod
        
        c_k, c_v = st.columns(2)
        kg = c_k.number_input(t['forms'][2], step=10.0, key=f"kg_{key_suffix}")
        val = c_v.number_input(t['forms'][3], step=100.0, key=f"val_{key_suffix}")
        
        current_stock = stock_real.get(prod, 0.0) if prod in stock_real else 0.0
        
        if prod in stock_real: 
            if current_stock <= 0: 
                st.error(f"⚠️ {t['alerts']['stock_out']}: {current_stock:.1f} kg")
            elif current_stock < 20: 
                st.warning(f"🟠 {t['alerts']['stock_low']}: {current_stock:.1f} kg")
            else: 
                st.success(f"✅ {t['alerts']['stock_ok']}: {current_stock:.1f} kg")
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        success_flag = False
        
        if st.button(t['forms'][4], type="primary", use_container_width=True):
            if emp and prod:
                if kg > current_stock:
                    st.error(f"🚫 {t['alerts']['err_stock']} {current_stock:.1f} kg {t['alerts']['try_sell']} {kg:.1f} kg.")
                else:
                    with st.spinner(f"⏳ {t['alerts']['saving']}"):
                        bk = get_book_direct()
                        sheet = bk.get_worksheet(0)
                        row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto"]
                        def do_write(): sheet.append_row(row)
                        success, error = safe_api_action(do_write)
                        if success:
                            log_action(bk, "VENTA", f"{emp} | {kg}kg | {prod}")
                            st.cache_data.clear() 
                            st.session_state.sale_key += 1
                            if PDF_AVAILABLE:
                                try:
                                    pdf_data = create_pdf(emp, prod, kg, val, st.session_state.username)
                                    st.download_button(t['dl_excel'], data=pdf_data, file_name=f"Recibo.pdf", mime="application/pdf")
                                except: pass
                            success_flag = True
                        else: st.error(f"Error: {error}")
        
        if success_flag:
            st.toast(t['alerts']['sold_ok'], icon="✅")
            time.sleep(0.5)
            st.rerun()

    st.divider()
    st.caption(t['alerts']['last_sales'])
    if not df_sales.empty:
        df_mini = df_sales[['Fecha_Registro', 'Empresa', 'Producto', 'Kg', 'Valor_BRL']].iloc[::-1].head(3)
        st.dataframe(df_mini, use_container_width=True, hide_index=True, column_config={
            'Valor_BRL': st.column_config.NumberColumn(format=f"{s} %.2f"),
            'Kg': st.column_config.NumberColumn(format="%.1f kg")
        })

@st.fragment
def render_stock_management(t, productos_all, df_stock_in):
    st.title(t['headers'][2])
    stk_suffix = str(st.session_state.stock_key)
    with st.container(border=True):
        st.caption(t['stock_add_title'])
        prod_stock = st.selectbox(t['forms'][1], ["✨ Novo..."] + productos_all, key=f"s_prod_{stk_suffix}")
        if prod_stock == "✨ Novo...": prod_stock = st.text_input(t['new_labels'][1], key=f"s_prod_txt_{stk_suffix}")
        
        c_k, c_u = st.columns(2)
        kg_stock = c_k.number_input("Kg (+)", step=10.0, key=f"s_kg_{stk_suffix}")
        user_stock = c_u.text_input(t['user_lbl'], value="CEO", key=f"s_usr_{stk_suffix}")
        
        success_stock = False
        
        if st.button(t['stock_btn'], type="primary", use_container_width=True):
            with st.spinner(f"{t['alerts']['adding']}"):
                bk = get_book_direct()
                try:
                    try: sh_stk = bk.worksheet("Estoque")
                    except: 
                        sh_stk = bk.add_worksheet(title="Estoque", rows=1000, cols=10)
                        sh_stk.append_row(["Data", "Produto", "Kg", "Usuario"])
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    def do_stock(): sh_stk.append_row([now, prod_stock, kg_stock, user_stock])
                    success, err = safe_api_action(do_stock)
                    if success:
                        log_action(bk, "STOCK_ADD", f"{prod_stock} | +{kg_stock}kg")
                        st.cache_data.clear()
                        st.session_state.stock_key += 1
                        success_stock = True
                    else: st.error(f"Error: {err}")
                except Exception as e: st.error(f"Error grave: {e}")
        
        if success_stock:
            st.toast(t['stock_msg'], icon="📦")
            time.sleep(0.5)
            st.rerun()

    st.write("")
    st.divider()
    
    # --- ZONA DE HISTÓRICO Y EDICIÓN ---
    c_laz1, c_laz2 = st.columns([3,1])
    c_laz1.subheader(t['hist_entries'])
    use_all = c_laz2.checkbox(t['alerts']['show_all'], value=False)
    
    filtro_stock = st.text_input(t['search_stk'], key="search_stk")
    
    if not df_stock_in.empty:
        if not use_all and not filtro_stock:
            df_view = df_stock_in.tail(50)
            st.caption(f"⚡ {t['alerts']['lazy_msg']}")
        else:
            df_view = df_stock_in
            
        if filtro_stock:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(filtro_stock, case=False)).any(axis=1)]
        
        # 1. TABLA EXCEL (Edición rápida)
        st.caption(f"{t['alerts']['excel_edit_mode']}")
        df_editor = df_view.iloc[::-1].copy()
        
        edited_df = st.data_editor(
            df_editor,
            num_rows="fixed",
            use_container_width=True,
            disabled=["Data"],
            key="stock_editor"
        )
        
        if st.button(t['alerts']['save_table'], key="save_stk_table", use_container_width=True):
            with st.spinner(f"{t['alerts']['updating']}"):
                bk = get_book_direct()
                sh_stk = bk.worksheet("Estoque")
                updated_count = 0
                for index, row in edited_df.iterrows():
                    cell = find_row_by_date(sh_stk, str(row['Data']))
                    if cell:
                        sh_stk.update_cell(cell.row, 2, row['Produto'])
                        sh_stk.update_cell(cell.row, 3, row['Kg'])
                        sh_stk.update_cell(cell.row, 4, row['Usuario'])
                        updated_count += 1
                
                if updated_count > 0:
                    log_action(bk, "EDIT_STOCK_TABLE", f"Modificados {updated_count} registros via Tabela")

                st.cache_data.clear()
                st.toast(f"{t['msgs'][3]} ({updated_count})", icon="💾")
                time.sleep(1)
                st.rerun()

        # 2. LISTA DE EDICIÓN INDIVIDUAL
        st.write("---")
        st.caption(f"{t['alerts']['manual_mode']}")
        
        to_edit_manual = df_view.iloc[::-1]
        
        for i, r in to_edit_manual.iterrows():
            row_label = f"📦 {r.get('Produto', '?')} | {r.get('Kg', 0)}kg"
            with st.expander(row_label):
                new_stk_prod = st.text_input(t['forms'][1], value=str(r.get('Produto', '')), key=f"ed_stk_p_{i}")
                new_stk_kg = st.number_input("Kg", value=float(r.get('Kg', 0)), step=1.0, key=f"ed_stk_k_{i}")
                
                c_btn_s1, c_btn_s2 = st.columns(2)
                
                if c_btn_s1.button(t['save_changes'], key=f"sav_stk_{i}", use_container_width=True):
                    with st.spinner(f"{t['alerts']['updating']}"):
                        bk = get_book_direct()
                        sh_stk = bk.worksheet("Estoque")
                        cell = find_row_by_date(sh_stk, str(r['Data']))
                        if cell:
                            def do_stk_update():
                                sh_stk.update_cell(cell.row, 2, new_stk_prod) 
                                sh_stk.update_cell(cell.row, 3, new_stk_kg)   
                            success, err = safe_api_action(do_stk_update)
                            if success: 
                                diffs = []
                                if str(r['Produto']) != str(new_stk_prod): diffs.append(f"Prod: {r['Produto']}->{new_stk_prod}")
                                if float(r['Kg']) != float(new_stk_kg): diffs.append(f"Kg: {r['Kg']}->{new_stk_kg}")
                                log_msg = f"Editado Stock: {r['Data']} | " + " | ".join(diffs)
                                log_action(bk, "EDIT_STOCK", log_msg)
                                st.cache_data.clear()
                                st.toast(t['msgs'][3], icon="💾")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"Error: {err}")
                        else: st.error("No encontré la fila.")

                if c_btn_s2.button(t['del_entry'], key=f"del_stk_{i}", type="secondary", use_container_width=True):
                    with st.spinner(f"{t['alerts']['deleting']}"):
                        bk = get_book_direct()
                        sh_stk = bk.worksheet("Estoque")
                        cell = find_row_by_date(sh_stk, str(r['Data']))
                        if cell:
                            def do_stk_del(): sh_stk.delete_rows(cell.row)
                            success, err = safe_api_action(do_stk_del)
                            if success: 
                                log_action(bk, "DEL_STOCK", f"Apagado: {r['Data']} - {r['Produto']}")
                                st.cache_data.clear()
                                st.toast(t['msgs'][1], icon="🗑️")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"Error: {err}")
                        else: st.error("Error.")

    else:
        st.info(t['msgs'][2])

    st.write("")
    with st.expander(t['wipe_stk_title']):
        st.warning(t['wipe_stk_warn'])
        check_wipe_stk = st.checkbox(t['wipe_stk_check'], key="chk_wipe_stk")
        if check_wipe_stk:
            wipe_success = False
            if st.button(t['wipe_stk_btn'], type="primary", use_container_width=True):
                with st.spinner(f"{t['alerts']['wiping']}"):
                    bk = get_book_direct()
                    try:
                        sh_stk = bk.worksheet("Estoque")
                        def do_wipe_stk():
                            sh_stk.clear()
                            sh_stk.append_row(["Data", "Produto", "Kg", "Usuario"])
                        success, err = safe_api_action(do_wipe_stk)
                        if success: 
                            log_action(bk, "WIPE_STOCK", "Tabela Estoque Zerada")
                            st.cache_data.clear()
                            wipe_success = True
                        else: st.error(f"Error: {err}")
                    except: st.error("No existe hoja Estoque")
            
            if wipe_success:
                st.toast(t['msgs'][1], icon="🔥")
                time.sleep(0.5)
                st.rerun()

@st.fragment
def render_sales_management(t, df_sales, s):
    st.title(t['admin_sales_title'])
    filtro = st.text_input(t['search_sales'], key="admin_search") 
    
    use_all = st.checkbox(t['alerts']['show_all'], value=False, key="all_sales")
    
    if not df_sales.empty:
        if not use_all and not filtro:
            df_filtered = df_sales.tail(50)
            st.caption(f"⚡ {t['alerts']['lazy_msg']}")
        else:
            df_filtered = df_sales
            
        if filtro:
            df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
            st.info(f"Resultados: {len(df_filtered)}")
        
        # MODO EXCEL
        st.caption(f"{t['alerts']['excel_edit_mode']}")
        df_editor_sales = df_filtered.iloc[::-1].copy()
        
        edited_sales = st.data_editor(
            df_editor_sales,
            use_container_width=True,
            disabled=["Fecha_Registro", "Comissao_BRL", "Mes_Lang", "Fecha_DT"], 
            key="sales_editor",
            column_config={
                "Kg": st.column_config.NumberColumn("Kg", min_value=0, step=1.0),
                "Valor_BRL": st.column_config.NumberColumn("Valor", min_value=0, step=10.0)
            }
        )
        
        if st.button(t['alerts']['save_table'], key="save_sales_table", use_container_width=True):
            with st.spinner(f"{t['alerts']['updating']}"):
                bk = get_book_direct()
                sh_sl = bk.get_worksheet(0)
                updated_count = 0
                for index, row in edited_sales.iterrows():
                    cell = find_row_by_date(sh_sl, str(row['Fecha_Registro']))
                    if cell:
                        sh_sl.update_cell(cell.row, 1, row['Empresa'])
                        sh_sl.update_cell(cell.row, 2, row['Producto'])
                        sh_sl.update_cell(cell.row, 3, row['Kg'])
                        sh_sl.update_cell(cell.row, 4, row['Valor_BRL'])
                        sh_sl.update_cell(cell.row, 5, float(row['Valor_BRL']) * 0.02)
                        updated_count += 1
                
                if updated_count > 0:
                    log_action(bk, "EDIT_SALES_TABLE", f"Modificados {updated_count} vendas via Tabela")

                st.cache_data.clear()
                st.toast(f"{t['msgs'][3]} ({updated_count})", icon="💾")
                time.sleep(1)
                st.rerun()
        
        # LISTA INDIVIDUAL
        st.write("---")
        st.caption(f"{t['alerts']['manual_mode']}")
        
        to_edit_sales = df_filtered.iloc[::-1]
        
        if not filtro and not use_all and len(to_edit_sales) > 20:
             st.info("Mostrando últimos 20. Usa el buscador para más.")
             to_edit_sales = to_edit_sales.head(20)

        for i, r in to_edit_sales.iterrows():
            with st.expander(f"💰 {r['Empresa']} | {r['Producto']}"):
                new_emp = st.text_input("Cliente", value=r['Empresa'], key=f"admin_emp_{i}")
                c_k, c_v = st.columns(2)
                new_kg = c_k.number_input("Kg", value=float(r['Kg']), key=f"k_{i}")
                new_val = c_v.number_input("Valor", value=float(r['Valor_BRL']), key=f"v_{i}")
                
                c_btn1, c_btn2 = st.columns(2)
                
                if c_btn1.button(t['save_changes'], key=f"save_{i}", use_container_width=True):
                    with st.spinner(f"{t['alerts']['updating']}"):
                        bk = get_book_direct()
                        sh_sl = bk.get_worksheet(0)
                        
                        cell = find_row_by_date(sh_sl, str(r['Fecha_Registro']))
                        if cell:
                            def do_update():
                                sh_sl.update_cell(cell.row, 1, new_emp)
                                sh_sl.update_cell(cell.row, 3, new_kg)
                                sh_sl.update_cell(cell.row, 4, new_val)
                                sh_sl.update_cell(cell.row, 5, new_val*0.02)
                            success, err = safe_api_action(do_update)
                            if success: 
                                diffs = []
                                if r['Empresa'] != new_emp: diffs.append(f"Cli: {r['Empresa']}->{new_emp}")
                                if float(r['Kg']) != float(new_kg): diffs.append(f"Kg: {r['Kg']}->{new_kg}")
                                if float(r['Valor_BRL']) != float(new_val): diffs.append(f"$: {r['Valor_BRL']}->{new_val}")
                                log_msg = f"Edit Venda: {r['Fecha_Registro']} | " + " | ".join(diffs)
                                log_action(bk, "EDIT_SALE", log_msg)
                                st.cache_data.clear()
                                st.toast(t['msgs'][3], icon="💾")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"Error: {err}")
                        else: st.error("No encontrado (Error fecha).")
                
                if c_btn2.button(t['del_entry'], key=f"del_{i}", type="secondary", use_container_width=True):
                    with st.spinner(f"{t['alerts']['deleting']}"):
                        bk = get_book_direct()
                        sh_sl = bk.get_worksheet(0)
                        cell = find_row_by_date(sh_sl, str(r['Fecha_Registro']))
                        if cell:
                            def do_del(): sh_sl.delete_rows(cell.row)
                            success, err = safe_api_action(do_del)
                            if success: 
                                log_action(bk, "DEL_SALE", f"Apagado: {r['Fecha_Registro']} - {r['Empresa']}")
                                st.cache_data.clear()
                                st.toast(t['msgs'][1], icon="🗑️")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"Error: {err}")
                        else: st.error("No encontrado.")
        
        st.write("")
        with st.expander(t['wipe_sales_title']):
            st.warning(t['wipe_stk_warn'])
            check_wipe_sales = st.checkbox(t['wipe_stk_check'], key="chk_wipe_sales")
            if check_wipe_sales:
                wipe_sales_flag = False
                if st.button(t['wipe_sales_btn'], type="primary", use_container_width=True):
                    with st.spinner(f"{t['alerts']['wiping']}"):
                        bk = get_book_direct()
                        sh_sl = bk.get_worksheet(0)
                        def do_wipe_sales():
                            sh_sl.clear()
                            sh_sl.append_row(["Empresa", "Producto", "Kg", "Valor_BRL", "Comissao_BRL", "Fecha_Registro", "Tipo"])
                        success, err = safe_api_action(do_wipe_sales)
                        if success: 
                            log_action(bk, "WIPE_SALES", "Tabela Vendas Zerada")
                            st.cache_data.clear()
                            wipe_sales_flag = True
                        else: st.error(f"Error: {err}")
                if wipe_sales_flag:
                    st.toast(t['msgs'][1], icon="🔥")
                    time.sleep(0.5)
                    st.rerun()
        
        # --- ZONA DE BACKUP ---
        st.divider()
        with st.expander(t['alerts']['backup_title']):
            st.info(t['alerts']['backup_desc'])
            if st.button(t['alerts']['backup_btn'], use_container_width=True):
                with st.spinner(t['alerts']['backup_load']):
                    bk = get_book_direct()
                    d_sales = pd.DataFrame(bk.get_worksheet(0).get_all_records())
                    d_stock = pd.DataFrame(bk.worksheet("Estoque").get_all_records())
                    d_hist = pd.DataFrame(bk.worksheet("Historial").get_all_records())
                    
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        d_sales.to_excel(writer, sheet_name='Ventas', index=False)
                        d_stock.to_excel(writer, sheet_name='Stock', index=False)
                        d_hist.to_excel(writer, sheet_name='Historial', index=False)
                    
                    st.download_button(
                        label="📥 Download",
                        data=buffer,
                        file_name=f"Backup_Xingu_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

@st.fragment
def render_log(t):
    st.title(t['headers'][3])
    col_btn, col_info = st.columns([1, 2])
    if col_btn.button("🔄 Cargar/Ocultar Historial", type="secondary", use_container_width=True):
        st.session_state.show_log = not st.session_state.show_log
        st.rerun()

    # --- FILTRO ACTIVO ---
    if st.session_state.log_filter_override:
        st.info(f"🔎 Filtrando por: **{st.session_state.log_filter_override}**")
        if st.button("❌ Limpar Filtro", use_container_width=True):
            st.session_state.log_filter_override = ""
            st.rerun()

    if st.session_state.show_log:
        try:
            bk = get_book_direct()
            sh_log = bk.worksheet("Historial")
            h_dt = pd.DataFrame(sh_log.get_all_records())
            if not h_dt.empty:
                show_log = h_dt.copy()
                if "Accion" in show_log.columns:
                    emoji_map = t['val_map'].copy()
                    show_log["Accion"] = show_log["Accion"].replace(emoji_map)
                show_log = show_log.rename(columns=t['col_map'])
                
                # APLICAR FILTRO MANUAL
                if st.session_state.log_filter_override:
                    mask = show_log.astype(str).apply(lambda x: x.str.contains(st.session_state.log_filter_override, case=False)).any(axis=1)
                    show_log = show_log[mask]

                # SELECCIÓN INTERACTIVA
                selection = st.dataframe(
                    show_log.iloc[::-1], 
                    use_container_width=True,
                    selection_mode="single-row",
                    on_select="rerun"
                )
                
                # LÓGICA DE "IR AL USUARIO"
                if selection.selection.rows:
                    idx = selection.selection.rows[0]
                    row_data = show_log.iloc[::-1].iloc[idx]
                    details = str(row_data.get(t['col_map']['Detalles'], ''))
                    parts = details.split('|')
                    possible_filter = ""
                    if len(parts) > 1:
                        possible_filter = parts[1].strip().split('->')[0].replace("Cli: ", "").replace("Prod: ", "").strip()
                    else:
                        parts_dash = details.split('-')
                        if len(parts_dash) > 1:
                             possible_filter = parts_dash[-1].strip()

                    if possible_filter:
                        st.info(f"Seleccionado: {possible_filter}")
                        if st.button(f"🔍 Filtrar historial por '{possible_filter}'", use_container_width=True):
                            st.session_state.log_filter_override = possible_filter
                            st.rerun()

                st.divider()
                st.markdown("### 🗑️")
                with st.expander(t['msgs'][4]):
                    rev_h = h_dt.iloc[::-1].reset_index()
                    opc_h = [f"{r['Fecha_Hora']} | {r['Accion']} | {r['Detalles']}" for i, r in rev_h.iterrows()]
                    sel_h = st.multiselect("Items", opc_h)
                    
                    if st.button(t['actions'][4], key="btn_h", type="primary", use_container_width=True):
                        if sel_h:
                            with st.spinner(f"{t['alerts']['deleting']}"):
                                dts_h = [x.split(" | ")[0] for x in sel_h]
                                all_vals = sh_log.get_all_values()
                                dels = []
                                for i, row in enumerate(all_vals):
                                    if i==0: continue
                                    if row[0] in dts_h: dels.append(i+1)
                                dels.sort(reverse=True)
                                
                                def do_log_del():
                                    for d in dels: sh_log.delete_rows(d)
                                
                                success, err = safe_api_action(do_log_del)
                                if success: 
                                    st.toast(t['msgs'][1], icon="🗑️")
                                    time.sleep(0.5)
                                    st.rerun()
                                else: st.error(f"Error: {err}")

                st.write("")
                col_danger1, col_danger2 = st.columns([3, 1])
                check_danger = col_danger1.checkbox(t['wipe_stk_check'])
                if check_danger:
                    if col_danger2.button("🔥 BORRAR LOG", type="primary", use_container_width=True):
                        with st.spinner(f"{t['alerts']['wiping']}"):
                            def do_wipe():
                                sh_log.clear()
                                sh_log.append_row(["Fecha_Hora", "Accion", "Detalles"])
                            success, err = safe_api_action(do_wipe)
                            if success: 
                                st.toast(t['msgs'][1], icon="🧹")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"Error: {err}")
            else:
                st.info(t['msgs'][2])
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Log hidden.")

# --- APP MAIN ---
def main():
    if not check_password(): return

    with st.sidebar:
        try: st.image(ICONO_APP, width=100) 
        except: st.markdown(f"<h1 style='text-align: center; font-size: 50px; margin:0;'>🍇</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{NOMBRE_EMPRESA}</h3>", unsafe_allow_html=True)
        lang = st.selectbox("Idioma", ["Português", "Español", "English"])
        t = TR.get(lang, TR["Português"]) 
        t["tabs"] = [t['tabs'][0], t['tabs'][1], t['tabs'][2], t['tabs'][3], t['tabs'][4]]
        st.caption("v100.0 Mobile Pro")
        if st.button("🔄", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button(t['logout'], use_container_width=True): st.session_state.authenticated = False; st.rerun()
    
    s = RATES[lang]["s"]; r = RATES[lang]["r"]

    # CARGA DATOS
    df_sales, df_stock_in = load_cached_data()
    if df_sales is None:
        st.error("⏳ Google Error 429. Wait 1 min.")
        st.stop()
    
    # CARGA CONFIG
    bk_conf = get_book_direct() 
    _, cfg = get_config(bk_conf)
    saved_meta = float(cfg.get('meta_goal', 0.0))
    saved_filter = cfg.get('stock_view_pref', "")

    # PROCESAMIENTO
    if not df_sales.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df_sales.columns: df_sales[c] = pd.to_numeric(df_sales[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df_sales['Empresa'].astype(str))))
        prods_sales = list(set(df_sales['Producto'].astype(str)))
        df_sales['Fecha_DT'] = pd.to_datetime(df_sales['Fecha_Registro'], errors='coerce')
        df_sales['Mes_Lang'] = df_sales['Fecha_DT'].dt.month.map(MONTHS_UI[lang])
    else: 
        empresas, prods_sales = [], []
        df_sales = pd.DataFrame(columns=['Producto', 'Kg', 'Valor_BRL', 'Fecha_Registro', 'Empresa', 'Comissao_BRL'])

    if not df_stock_in.empty:
        df_stock_in['Kg'] = pd.to_numeric(df_stock_in['Kg'], errors='coerce').fillna(0)
        prods_stock = list(set(df_stock_in['Produto'].astype(str)))
    else: prods_stock = []

    productos_all = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_sales + prods_stock)))

    stock_real = {}
    sales_real = {} 
    for p in productos_all:
        total_in = df_stock_in[df_stock_in['Produto'] == p]['Kg'].sum() if not df_stock_in.empty else 0
        total_out = df_sales[df_sales['Producto'] == p]['Kg'].sum() if not df_sales.empty else 0
        stock_real[p] = total_in - total_out
        sales_real[p] = total_out 

    # SIDEBAR
    ahora = datetime.now(); periodo_clave = ahora.strftime("%Y-%m")
    with st.sidebar:
        st.write(f"**{t['goal_lbl']} {MESES_UI_SIDEBAR[ahora.month]}**")
        meta = st.number_input("Meta", value=saved_meta, step=1000.0, label_visibility="collapsed")
        if st.button(t['goal_btn'], use_container_width=True):
            bk = get_book_direct()
            save_conf(bk, "meta_goal", meta)
            st.toast("Meta Atualizada", icon="🎯")
            time.sleep(0.5); st.rerun()
        val_mes = df_sales[df_sales['Fecha_Registro'].str.contains(periodo_clave, na=False)]['Valor_BRL'].sum() * r if not df_sales.empty else 0
        if meta > 0:
            st.progress(min(val_mes/meta, 1.0))
            st.caption(f"{val_mes/meta*100:.1f}% ({s} {val_mes:,.0f} / {s} {meta:,.0f})")
        st.divider()
        if not df_sales.empty:
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_ex = df_sales.copy()
                    df_ex['Fecha_Clean'] = df_ex['Fecha_DT'].dt.strftime('%d/%m/%Y %H:%M')
                    data_final = df_ex[['Fecha_Clean', 'Mes_Lang', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']].copy()
                    sheet_name = 'Reporte'
                    
                    data_final.to_excel(writer, index=False, sheet_name=sheet_name, startrow=5, header=False)
                    workbook = writer.book; ws = writer.sheets[sheet_name]
                    ws.hide_gridlines(2)
                    
                    fmt_kpi_label = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'font_color': '#718096'})
                    fmt_kpi_num = workbook.add_format({'font_name': 'Calibri', 'font_size': 14, 'bold': True, 'font_color': '#2B6CB0'})
                    fmt_head = workbook.add_format({'bold': True, 'bg_color': '#F7FAFC', 'font_color': '#4A5568', 'bottom': 1, 'bottom_color': '#E2E8F0', 'align': 'center'})
                    fmt_data = workbook.add_format({'font_name': 'Calibri', 'align': 'center'})
                    fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00', 'font_name': 'Calibri'})
                    fmt_num = workbook.add_format({'num_format': '0.0', 'font_name': 'Calibri', 'align': 'center'})
                    fmt_total = workbook.add_format({'bold': True, 'top': 1, 'top_color': '#CBD5E0', 'font_color': '#2D3748'})
                    
                    ws.write(1, 1, "Vendas Totais", fmt_kpi_label)
                    ws.write(2, 1, f"R$ {data_final['Valor_BRL'].sum():,.2f}", fmt_kpi_num)
                    ws.write(1, 3, "Volume (Kg)", fmt_kpi_label)
                    ws.write(2, 3, f"{data_final['Kg'].sum():,.1f} Kg", fmt_kpi_num)
                    ws.write(1, 5, "Comissao", fmt_kpi_label)
                    ws.write(2, 5, f"R$ {data_final['Comissao_BRL'].sum():,.2f}", fmt_kpi_num)

                    xls_headers = t.get('xls_head', ["Fecha", "Mes", "Empresa", "Producto", "Kg", "Valor", "Comisión"])
                    for col_num, h in enumerate(xls_headers): ws.write(4, col_num, h, fmt_head)
                    
                    ws.set_column('A:A', 18, fmt_data); ws.set_column('B:B', 12, fmt_data); ws.set_column('C:D', 22, fmt_data)
                    ws.set_column('E:E', 12, fmt_num); ws.set_column('F:G', 18, fmt_money)
                    
                    lr = len(data_final) + 5
                    ws.write(lr, 3, t.get('xls_tot', "TOTAL:"), fmt_total)
                    ws.write(lr, 4, data_final['Kg'].sum(), fmt_total)
                    ws.write(lr, 5, data_final['Valor_BRL'].sum(), fmt_total)
                    ws.write(lr, 6, data_final['Comissao_BRL'].sum(), fmt_total)

                    chart = workbook.add_chart({'type': 'column'})
                    chart.add_series({
                        'name':       'Vendas por Produto',
                        'categories': [sheet_name, 5, 3, lr-1, 3],
                        'values':     [sheet_name, 5, 5, lr-1, 5],
                    })
                    chart.set_title({'name': 'Vendas vs Produto'})
                    chart.set_style(10)
                    ws.insert_chart('H2', chart)

                st.download_button(t['dl_excel'], data=buffer, file_name=f"Reporte_Dashboard_{datetime.now().strftime('%Y-%m-%d')}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
            except Exception as ex: st.warning(f"⚠️ ({ex})")

    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs(t['tabs'])
    with tab1: render_dashboard(t, df_sales, stock_real, sales_real, prods_stock, prods_sales, s, r, lang, saved_filter)
    with tab2: render_new_sale(t, empresas, productos_all, stock_real, df_sales, s)
    with tab3: render_stock_management(t, productos_all, df_stock_in)
    with tab4: render_sales_management(t, df_sales, s)
    with tab5: render_log(t)

if __name__ == "__main__":
    main()
