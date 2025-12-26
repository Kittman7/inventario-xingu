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
CONTRASEÑA_MAESTRA = "julio777" 
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

# --- LOGIN ---
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

# --- DICCIONARIO ---
TR = {
    "Português": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nova Venda", "🛠️ Admin (Stock)", "📜 Log"],
        "metrics": ["Faturamento", "Volume Vendido", "Comissão", "Ticket Médio", "Melhor Cliente"],
        "stock_add_title": "📦 Adicionar Estoque (Entradas)",
        "stock_btn": "➕ Adicionar ao Estoque",
        "stock_alert": "Estoque Atual (Entradas - Vendas)",
        "table_title": "Detalhes",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar Venda"],
        "actions": ["Salvar", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk_label": "Gestão em Massa",
        "clean_hist_label": "Limpeza de Histórico",
        "dl_excel": "📗 Baixar Relatório",
        "logout": "🔒 Sair",
        "new_labels": ["Nome Cliente:", "Nome Produto:"],
        "dash_cols": {"val": "Valor", "com": "Comissão", "kg": "Kg"},
        "msgs": ["Sucesso!", "Apagado!", "Sem dados", "Atualizado!", "Seleccione items"],
        "stock_msg": "Estoque Adicionado!",
        "install": "📲 Instalar: Menu -> Adicionar à Tela de Início"
    },
    "Español": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nueva Venta", "🛠️ Admin (Stock)", "📜 Log"],
        "metrics": ["Facturación", "Volumen Vendido", "Comisión", "Ticket Medio", "Top Cliente"],
        "stock_add_title": "📦 Añadir Stock (Entradas)",
        "stock_btn": "➕ Sumar al Stock",
        "stock_alert": "Stock Actual (Entradas - Ventas)",
        "table_title": "Detalles",
        "forms": ["Cliente", "Producto", "Kg", "Valor ($)", "✅ Confirmar Venta"],
        "actions": ["Guardar", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk_label": "Gestión Masiva",
        "clean_hist_label": "Limpieza de Historial",
        "dl_excel": "📗 Bajar Reporte",
        "logout": "🔒 Salir",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "dash_cols": {"val": "Valor", "com": "Comisión", "kg": "Kg"},
        "msgs": ["¡Éxito!", "¡Borrado!", "Sin datos", "¡Actualizado!", "Seleccione items"],
        "stock_msg": "¡Stock Añadido!",
        "install": "📲 Instalar: Menú -> Agregar a Pantalla de Inicio"
    },
    "English": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ New Sale", "🛠️ Admin (Stock)", "📜 Log"],
        "metrics": ["Revenue", "Volume Sold", "Commission", "Avg Ticket", "Top Client"],
        "stock_add_title": "📦 Add Stock (Inputs)",
        "stock_btn": "➕ Add to Stock",
        "stock_alert": "Current Stock (Inputs - Sales)",
        "table_title": "Details",
        "forms": ["Client", "Product", "Kg", "Value", "✅ Confirm Sale"],
        "actions": ["Save", "DELETE", "Search...", "✨ New...", "🗑️ Delete Selection"],
        "bulk_label": "Bulk Management",
        "clean_hist_label": "Clear History",
        "dl_excel": "📗 Download Report",
        "logout": "🔒 Logout",
        "new_labels": ["Client Name:", "Product Name:"],
        "dash_cols": {"val": "Value", "com": "Comm", "kg": "Kg"},
        "msgs": ["Success!", "Deleted!", "No data", "Updated!", "Select items"],
        "stock_msg": "Stock Added!",
        "install": "📲 Install: Menu -> Add to Home Screen"
    }
}
RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }

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

# --- APP ---
def main():
    if not check_password(): return

    with st.sidebar:
        st.markdown(f"<h1 style='text-align: center; font-size: 50px; margin:0;'>{ICONO_APP}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{NOMBRE_EMPRESA}</h3>", unsafe_allow_html=True)
        lang = st.selectbox("Idioma", ["Português", "Español", "English"])
        t = TR.get(lang, TR["Português"]) 
        st.caption("v51.0 Real Stock")
        if st.button(t['logout']): st.session_state.authenticated = False; st.rerun()
    
    s = RATES[lang]["s"]; r = RATES[lang]["r"]

    try:
        book = get_data()
        sheet_sales = book.sheet1
        
        # INTENTAR CARGAR LA HOJA DE STOCK
        try:
            sheet_stock = book.worksheet("Estoque")
            df_stock_in = pd.DataFrame(sheet_stock.get_all_records())
        except:
            st.error("⚠️ Faltan datos: Crea una hoja llamada 'Estoque' con columnas: Data, Produto, Kg, Usuario")
            df_stock_in = pd.DataFrame(columns=["Data", "Produto", "Kg", "Usuario"]) # Fallback vacío
            sheet_stock = None

        df_sales = pd.DataFrame(sheet_sales.get_all_records())

    except: st.error("DB Error"); st.stop()

    # --- PROCESAMIENTO DE DATOS ---
    # 1. Ventas
    if not df_sales.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df_sales.columns: df_sales[c] = pd.to_numeric(df_sales[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df_sales['Empresa'].astype(str))))
        prods_sales = list(set(df_sales['Producto'].astype(str)))
    else: 
        empresas, prods_sales = [], []
        df_sales = pd.DataFrame(columns=['Producto', 'Kg', 'Valor_BRL', 'Fecha_Registro'])

    # 2. Stock (Entradas)
    if not df_stock_in.empty:
        df_stock_in['Kg'] = pd.to_numeric(df_stock_in['Kg'], errors='coerce').fillna(0)
        prods_stock = list(set(df_stock_in['Produto'].astype(str)))
    else:
        prods_stock = []

    # Lista unificada de productos
    productos_all = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_sales + prods_stock)))

    # --- CALCULO DE STOCK REAL ---
    # Stock Real = Total Entradas - Total Salidas
    stock_real = {}
    for p in productos_all:
        total_in = df_stock_in[df_stock_in['Produto'] == p]['Kg'].sum() if not df_stock_in.empty else 0
        total_out = df_sales[df_sales['Producto'] == p]['Kg'].sum() if not df_sales.empty else 0
        stock_real[p] = total_in - total_out

    tab1, tab2, tab3, tab4 = st.tabs(t['tabs'])

    # 1. DASHBOARD (STOCK REAL)
    with tab1:
        st.title(t['headers'][0])
        
        # KPIs Financieros
        if not df_sales.empty:
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {(df_sales['Valor_BRL'].sum() * r):,.0f}")
            k2.metric(t['metrics'][1], f"{df_sales['Kg'].sum():,.0f} kg")
            k3.metric(t['metrics'][2], f"{s} {(df_sales['Valor_BRL'].sum()*0.02*r):,.0f}")
        
        st.divider()
        
        # --- ZONA DE STOCK REAL ---
        st.subheader(t['stock_alert'])
        if stock_real:
            # Ordenar por stock descendente
            for p, kg_left in sorted(stock_real.items(), key=lambda item: item[1], reverse=True):
                # Solo mostrar si hay movimiento (entrada o salida)
                if kg_left != 0 or p in prods_stock or p in prods_sales:
                    col_s1, col_s2 = st.columns([3, 1])
                    
                    # Color de la barra
                    color_barra = "normal" 
                    if kg_left < 50: color_barra = "off" # Rojo si es bajo (simulado)
                    
                    # Barra visual (Simulamos un tope de 1000kg para visualizar la barra)
                    # La barra muestra lo que QUEDA
                    pct = max(0.0, min(kg_left / 1000.0, 1.0))
                    
                    col_s1.progress(pct, text=f"📦 **{p}**: {kg_left:,.1f} kg Restantes")
                    
                    if kg_left < 0:
                        col_s2.error(f"⚠️ Negativo ({kg_left}kg)")
                    elif kg_left < 50:
                        col_s2.warning("⚠️ Poco Stock")
                    else:
                        col_s2.success("✅ OK")
        else:
            st.info("Sin datos de stock.")

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
            
            # Mostrar stock disponible al vender
            if prod in stock_real:
                st.caption(f"Stock disponible: {stock_real[prod]:.1f} kg")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['forms'][4], type="primary"):
                if emp and prod:
                    # Validar si hay stock (Opcional: permitir negativo)
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto"]
                    sheet_sales.append_row(row)
                    log_action(book, "VENTA", f"{emp} | {kg}kg | {prod}") # Cambie log code
                    st.success(t['msgs'][0])
                    
                    # PDF
                    if PDF_AVAILABLE:
                        try:
                            pdf_data = create_pdf(emp, prod, kg, val, st.session_state.username)
                            st.download_button(t['pdf'], data=pdf_data, file_name=f"Recibo.pdf", mime="application/pdf")
                        except: pass
                    
                    time.sleep(2); st.rerun()

    # 3. ADMIN & STOCK
    with tab3:
        st.header(t['stock_add_title'])
        
        # --- FORMULARIO AÑADIR STOCK ---
        with st.container(border=True):
            c_st1, c_st2, c_st3 = st.columns([2, 1, 1])
            
            # Selector de producto (permite escribir uno nuevo)
            prod_stock = c_st1.selectbox("Produto / Product", ["✨ Novo..."] + productos_all, key="stock_prod")
            if prod_stock == "✨ Novo...":
                prod_stock = c_st1.text_input("Nome do Produto", key="stock_prod_new")
            
            kg_stock = c_st2.number_input("Kg (+)", step=10.0, key="stock_kg")
            
            # Botón Añadir
            if c_st3.button(t['stock_btn'], type="primary"):
                if prod_stock and kg_stock > 0 and sheet_stock:
                    # Guardar en Hoja 'Estoque'
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user = st.session_state.username
                    sheet_stock.append_row([now, prod_stock, kg_stock, user])
                    
                    # Guardar en Log
                    log_action(book, "STOCK_ADD", f"{prod_stock} | +{kg_stock}kg")
                    
                    st.success(t['stock_msg'])
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Error: Hoja 'Estoque' no existe o datos inválidos.")

        st.divider()
        
        # --- BORRADO MASIVO (VENTAS) ---
        st.subheader("Gestión de Ventas")
        filtro = st.text_input(t['actions'][2], key="admin_search") 
        if not df_sales.empty:
            df_s = df_sales[df_sales.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df_sales.tail(5).iloc[::-1]
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
                    # Mapeo de Emojis extendido
                    emoji_map = t['val_map'].copy()
                    emoji_map["STOCK_ADD"] = "📦 Entrada Stock" # Nuevo Emoji
                    show_log["Accion"] = show_log["Accion"].replace(emoji_map)
                
                show_log = show_log.rename(columns=t['col_map'])
                st.dataframe(show_log.iloc[::-1], use_container_width=True)
        except: st.write("Log vacío")

if __name__ == "__main__":
    main()
