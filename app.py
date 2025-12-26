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

# INTENTO DE IMPORTAR FPDF (Para evitar errores si falta)
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

# USUARIOS (Usuario: Contraseña)
USUARIOS = {
    "julio": "777",
    "admin": "admin"
}
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

# --- ESTILO CSS ---
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

# --- LOGIN SEGURO ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = "invitado"

    if st.session_state.authenticated:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA}</h1>", unsafe_allow_html=True)
        st.write("")
        user_input = st.text_input("Usuario")
        pass_input = st.text_input("Senha / Contraseña", type="password")
        
        if st.button("Entrar", type="primary"):
            u = user_input.strip().lower()
            p = pass_input.strip()
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.authenticated = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("🚫 Incorrecto")
    return False

# --- CLASE PDF (SOLO SI ESTÁ DISPONIBLE) ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'{NOMBRE_EMPRESA} - Recibo', 0, 1, 'C')
            self.ln(5)

    def create_pdf(cliente, producto, kg, valor, vendedor):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(200, 10, txt=f"Vendedor: {vendedor.upper()}", ln=True)
        pdf.line(10, 30, 200, 30); pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True); pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.cell(100, 10, txt="Produto", border=1)
        pdf.cell(40, 10, txt="Kg", border=1)
        pdf.cell(50, 10, txt="Valor", border=1); pdf.ln()
        pdf.cell(100, 10, txt=f"{producto}", border=1)
        pdf.cell(40, 10, txt=f"{kg}", border=1)
        pdf.cell(50, 10, txt=f"R$ {valor:,.2f}", border=1)
        pdf.ln(20)
        pdf.cell(0, 10, txt="Obrigado!", ln=True, align='C')
        return pdf.output(dest='S').encode('latin-1')

# --- DICCIONARIO DE IDIOMAS (CORREGIDO Y VERIFICADO) ---
TR = {
    "Português": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nova Venda", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venda", "Gestão", "Auditoria"],
        "metrics": ["Total R$", "Volume (Kg)", "Comissão", "Ticket Médio", "Top Cliente"],
        "charts": ["Tendência", "Mix Produtos", "Por Empresa"],
        "table_title": "Detalhes",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar"],
        "actions": ["Salvar", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk": "Gestão em Massa",
        "clean": "Limpar Histórico",
        "dl_excel": "📗 Baixar Excel",
        "logout": "🔒 Sair",
        "goal_lbl": "🎯 Meta de", 
        "goal_btn": "💾 Salvar Meta",
        "msgs": ["Sucesso!", "Apagado!", "Sem dados", "Atualizado!"],
        "pdf": "📄 Baixar Recibo",
        "stock_t": "📦 Estoque",
        "new_labels": ["Nome Cliente:", "Nome Produto:"], # AQUÍ ESTÁ LA CLAVE QUE FALTABA
        "dash_cols": {"val": "Valor", "com": "Comissão", "kg": "Kg"},
        "install": "📲 Instalar: Menu -> Adicionar à Tela de Início"
    },
    "Español": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nueva Venta", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venta", "Gestión", "Auditoría"],
        "metrics": ["Total $", "Volumen (Kg)", "Comisión", "Ticket Medio", "Top Cliente"],
        "charts": ["Tendencia", "Mix Productos", "Por Empresa"],
        "table_title": "Detalles",
        "forms": ["Cliente", "Producto", "Kg", "Valor ($)", "✅ Confirmar"],
        "actions": ["Guardar", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk": "Gestión Masiva",
        "clean": "Limpiar Historial",
        "dl_excel": "📗 Bajar Excel",
        "logout": "🔒 Salir",
        "goal_lbl": "🎯 Meta de",
        "goal_btn": "💾 Salvar Meta",
        "msgs": ["¡Éxito!", "¡Borrado!", "Sin datos", "¡Actualizado!"],
        "pdf": "📄 Bajar Recibo",
        "stock_t": "📦 Stock",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"], # AQUÍ TAMBIÉN
        "dash_cols": {"val": "Valor", "com": "Comisión", "kg": "Kg"},
        "install": "📲 Instalar: Menú -> Agregar a Pantalla de Inicio"
    },
    "English": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ New Sale", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "New Sale", "Admin", "Log"],
        "metrics": ["Total", "Volume (Kg)", "Commission", "Avg Ticket", "Top Client"],
        "charts": ["Trend", "Mix", "By Company"],
        "table_title": "Details",
        "forms": ["Client", "Product", "Kg", "Value", "✅ Confirm"],
        "actions": ["Save", "DELETE", "Search...", "✨ New...", "🗑️ Bulk Delete"],
        "bulk": "Bulk Action",
        "clean": "Clear Log",
        "dl_excel": "📗 Download Excel",
        "logout": "🔒 Logout",
        "goal_lbl": "🎯 Goal for",
        "goal_btn": "💾 Save Goal",
        "msgs": ["Success!", "Deleted!", "No data", "Updated!"],
        "pdf": "📄 Download Receipt",
        "stock_t": "📦 Stock",
        "new_labels": ["Client Name:", "Product Name:"], # Y AQUÍ
        "dash_cols": {"val": "Value", "com": "Comm", "kg": "Kg"},
        "install": "📲 Install: Menu -> Add to Home Screen"
    }
}

RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }
MESES_UI = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# --- CONEXIÓN ---
def get_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    book = client.open("Inventario_Xingu_DB")
    return book

def log_action(book, action, detail):
    try:
        user = st.session_state.get('username', 'anon')
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, f"{detail} ({user})"])
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

# --- APP PRINCIPAL ---
def main():
    if not check_password(): return

    with st.sidebar:
        st.markdown(f"<h1 style='text-align: center; font-size: 50px; margin:0;'>{ICONO_APP}</h1>", unsafe_allow_html=True)
        st.caption(f"👤 {st.session_state.username.upper()}")
        lang = st.selectbox("Idioma", ["Português", "Español", "English"])
        
        # --- FIX PARA DICCIONARIO ---
        # Si por alguna razón falla el idioma, usa Portugués por defecto para no romper la app
        t = TR.get(lang, TR["Português"]) 
        
        st.info(t["install"])
        st.markdown("---")
        st.caption("v40.0 Stable")
    
    s = RATES[lang]["s"]
    r = RATES[lang]["r"]

    try:
        book = get_data()
        sheet = book.sheet1
        df = pd.DataFrame(sheet.get_all_records())
    except: st.error("Error DB"); st.stop()

    if not df.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df['Empresa'].astype(str))))
        prods_db = sorted(list(set(df['Producto'].astype(str))))
    else: empresas, prods_db = [], []
    
    productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_db)))
    ahora = datetime.now()
    periodo_clave = ahora.strftime("%Y-%m")

    # SIDEBAR
    with st.sidebar:
        st.write(f"**{t['goal_lbl']} {MESES_UI[ahora.month]}**")
        db_goal = get_goal(book, periodo_clave)
        meta = st.number_input("Meta", value=db_goal, step=1000.0, label_visibility="collapsed")
        if st.button(t['goal_btn']):
            log_action(book, "META_UPDATE", f"{periodo_clave}|{meta}")
            st.success("OK!"); time.sleep(1); st.rerun()
        
        val_mes = df[df['Fecha_Registro'].str.contains(periodo_clave, na=False)]['Valor_BRL'].sum() * r if not df.empty else 0
        if meta > 0:
            st.progress(min(val_mes/meta, 1.0))
            st.caption(f"{val_mes/meta*100:.1f}% ({s} {val_mes:,.0f} / {s} {meta:,.0f})")
        
        st.divider()
        if not df.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer) as writer: df.to_excel(writer, index=False)
            st.download_button(t['dl_excel'], data=buffer, file_name="Data.xlsx")
        
        if st.button(t['logout']): st.session_state.authenticated = False; st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(t['tabs'])

    # 1. DASHBOARD
    with tab1:
        if not df.empty:
            total = df['Valor_BRL'].sum() * r
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {total:,.0f}")
            k2.metric(t['metrics'][1], f"{df['Kg'].sum():,.0f} kg")
            k3.metric(t['metrics'][2], f"{s} {(df['Valor_BRL'].sum()*0.02*r):,.0f}")
            
            st.divider()
            st.subheader(t['stock_t'])
            stock = df.groupby('Producto')['Kg'].sum().sort_values(ascending=False).head(3)
            for p, q in stock.items():
                st.progress(min(q/1000, 1.0), text=f"{p}: {q:,.0f} kg")
            
            st.divider()
            st.subheader(t['table_title'])
            df_show = df.copy()
            # Mostramos las columnas correctas
            st.dataframe(df_show[['Empresa', 'Producto', 'Kg', 'Valor_BRL']].iloc[::-1], use_container_width=True, hide_index=True)

    # 2. VENDER
    with tab2:
        st.header(t['headers'][1])
        with st.container(border=True):
            c1, c2 = st.columns(2)
            
            # --- CORRECCIÓN: Usamos indices seguros para "Novo" ---
            opcion_nuevo = t['actions'][3] # Corresponde a "✨ Novo..."
            
            sel_emp = c1.selectbox(t['forms'][0], [opcion_nuevo] + empresas)
            # Aquí es donde fallaba antes: ahora t['new_labels'] existe
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == opcion_nuevo else sel_emp
            
            sel_prod = c2.selectbox(t['forms'][1], [opcion_nuevo] + productos)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == opcion_nuevo else sel_prod
            
            kg = c1.number_input(t['forms'][2], step=10.0)
            val = c2.number_input(t['forms'][3], step=100.0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['forms'][4], type="primary"):
                if emp and prod:
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto"]
                    sheet.append_row(row)
                    log_action(book, "NEW", f"{emp} | {kg}kg")
                    st.success(t['msgs'][0])
                    
                    if PDF_AVAILABLE:
                        try:
                            pdf_data = create_pdf(emp, prod, kg, val, st.session_state.username)
                            st.download_button(t['pdf'], data=pdf_data, file_name=f"Recibo.pdf", mime="application/pdf")
                        except: pass
                    
                    time.sleep(2)
                    st.rerun()

    # 3. ADMIN
    with tab3:
        filtro = st.text_input(t['actions'][2]) # Buscar
        if not df.empty:
            df_s = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df.tail(5).iloc[::-1]
            for i, r in df_s.iterrows():
                with st.expander(f"{r['Empresa']} | {r['Producto']}"):
                    if st.button(t['actions'][1], key=f"d{i}"): # Borrar
                        try:
                            cell = sheet.find(str(r['Fecha_Registro']))
                            sheet.delete_rows(cell.row)
                            st.success(t['msgs'][1])
                            time.sleep(1); st.rerun()
                        except: st.error("Error deleting")

    # 4. LOG
    with tab4:
        try:
            st.dataframe(pd.DataFrame(book.worksheet("Historial").get_all_records()).iloc[::-1], use_container_width=True)
        except: st.write("Log vacío")

if __name__ == "__main__":
    main()
