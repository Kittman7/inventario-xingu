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

# INTENTO DE IMPORTAR FPDF (Para que no falle si falta)
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

# 👤 USUARIOS Y CONTRASEÑAS (Multi-Usuario)
USUARIOS = {
    "julio": "777",
    "vendedor": "1234",
    "admin": "admin"
}
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

# --- ESTILO CSS PRO ---
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

# --- SISTEMA DE LOGIN MULTI-USUARIO ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    if st.session_state.authenticated:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA} Login</h1>", unsafe_allow_html=True)
        st.write("")
        
        user_input = st.text_input("Usuario / User")
        pass_input = st.text_input("Senha / Contraseña", type="password")
        
        if st.button("Entrar / Login", type="primary"):
            user_clean = user_input.strip().lower()
            pass_clean = pass_input.strip()
            
            if user_clean in USUARIOS and USUARIOS[user_clean] == pass_clean:
                st.session_state.authenticated = True
                st.session_state.username = user_clean
                st.rerun()
            else:
                st.error("🚫 Acceso Denegado")
    return False

# --- GENERADOR DE RECIBOS PDF ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'{NOMBRE_EMPRESA} - Recibo de Venda', 0, 1, 'C')
            self.ln(5)

    def create_pdf(cliente, producto, kg, valor, vendedor):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(200, 10, txt=f"Vendedor: {vendedor.upper()}", ln=True)
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.cell(100, 10, txt="Produto", border=1)
        pdf.cell(40, 10, txt="Qtd (Kg)", border=1)
        pdf.cell(50, 10, txt="Valor", border=1)
        pdf.ln()
        pdf.cell(100, 10, txt=f"{producto}", border=1)
        pdf.cell(40, 10, txt=f"{kg}", border=1)
        pdf.cell(50, 10, txt=f"R$ {valor:,.2f}", border=1)
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, txt="Obrigado pela preferencia!", ln=True, align='C')
        return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURACIÓN GLOBAL ---
MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
MONTHS_UI = {
    "Português": MESES_PT,
    "Español": {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"},
    "English": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
}

# --- IDIOMAS (AQUÍ ESTABA EL ERROR - YA CORREGIDO) ---
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
        "logout_label": "🔒 Sair",
        "goal_label": "🎯 Meta de", 
        "goal_save": "💾 Salvar Meta do Mês",
        "goal_text": "Progresso Mensal",
        "msgs": ["Venda Registrada!", "Apagado!", "Sem dados", "Meta Atualizada!"],
        "pdf_btn": "📄 Baixar Recibo (PDF)",
        "stock_title": "📦 Alerta de Estoque",
        "stock_desc": "Vendas totais vs Limite teórico",
        "col_map": {"Fecha_Hora": "📅 Data", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "dash_cols": {"emp": "Empresa", "prod": "Produto", "kg": "Qtd", "val": "Valor", "com": "Comissão", "mes": "Mês"},
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Massa", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "install_guide": "📲 **Como instalar no celular:**\n\n1. No Chrome/Safari, toque em **Compartilhar** o **Menu** (três pontos).\n2. Selecione **'Adicionar à Tela de Início'**.\n3. Pronto! Agora é um App nativo.",
        "new_labels": ["Nome Cliente:", "Nome Produto:"] # <--- ESTA LÍNEA FALTABA Y CAUSABA EL ERROR
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
        "logout_label": "🔒 Salir",
        "goal_label": "🎯 Meta de",
        "goal_save": "💾 Salvar Meta del Mes",
        "goal_text": "Progreso Mensual",
        "msgs": ["¡Venta Registrada!", "¡Borrado!", "Sin datos", "¡Meta Actualizada!"],
        "pdf_btn": "📄 Descargar Recibo (PDF)",
        "stock_title": "📦 Alerta de Stock",
        "stock_desc": "Ventas totales vs Límite teórico",
        "col_map": {"Fecha_Hora": "📅 Fecha", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "dash_cols": {"emp": "Empresa", "prod": "Producto", "kg": "Cant", "val": "Valor", "com": "Comisión", "mes": "Mes"},
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Masa", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"},
        "install_guide": "📲 **Cómo instalar en el celular:**\n\n1. En Chrome/Safari, toca **Compartir** o el **Menú** (tres puntos).\n2. Selecciona **'Agregar a Pantalla de Inicio'**.\n3. ¡Listo! Ahora es una App nativa.",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"] # <--- ESTA LÍNEA FALTABA Y CAUSABA EL ERROR
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
        "logout_label": "🔒 Logout",
        "goal_label": "🎯 Goal for",
        "goal_save": "💾 Save Goal",
        "goal_text": "Monthly Progress",
        "msgs": ["Sale Registered!", "Deleted!", "No data", "Goal Updated!"],
        "pdf_btn": "📄 Download Receipt (PDF)",
        "stock_title": "📦 Stock Alert",
        "stock_desc": "Total sales vs Theoretical limit",
        "col_map": {"Fecha_Hora": "📅 Date", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "dash_cols": {"emp": "Company", "prod": "Product", "kg": "Qty", "val": "Value", "com": "Commission", "mes": "Month"},
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Deleted", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean", "META_UPDATE": "🎯 Goal"},
        "install_guide": "📲 **How to install on mobile:**\n\n1. In Chrome/Safari, tap **Share** or **Menu** (three dots).\n2. Select **'Add to Home Screen'**.\n3. Done! It's now a native App.",
        "new_labels": ["Client Name:", "Product Name:"] # <--- ESTA LÍNEA FALTABA Y CAUSABA EL ERROR
    }
}

RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }

# --- CONEXIÓN ---
def get_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    book = client.open("Inventario_Xingu_DB")
    return book

def log_action(book, action, detail):
    try:
        # LOG INCLUYE EL USUARIO ACTUAL
        user = st.session_state.get('username', 'anon')
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, f"{detail} (User: {user})"])
    except: pass

def get_monthly_goal_from_db(book, current_period_key):
    try:
        sheet_log = book.worksheet("Historial")
        rows = sheet_log.get_all_values()
        for row in reversed(rows[1:]): 
            if len(row) >= 3 and row[1] == 'META_UPDATE' and "|" in str(row[2]):
                p, v = str(row[2]).split("|")
                if p == current_period_key: return float(v)
    except: pass
    return 0.0

# --- APP PRINCIPAL ---
def main():
    if not check_password(): return

    # --- SIDEBAR COMPLETA ---
    with st.sidebar:
        st.markdown(f"<h1 style='text-align: center; font-size: 60px; margin-bottom: 0;'>{ICONO_APP}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{NOMBRE_EMPRESA}</h3>", unsafe_allow_html=True)
        
        # SALUDO AL USUARIO
        st.caption(f"👤 Logged as: **{st.session_state.username.upper()}**")
        
        lang = st.selectbox("Language / Idioma", ["Português", "Español", "English"])
        
        # -- SEGURO CONTRA ERROR DE IDIOMA --
        t = TR.get(lang, TR["Português"]) # Si falla, usa portugués
        
        with st.expander("📲 Instalar App"):
            st.info(t.get("install_guide", "Menu -> Add to Home Screen"))

        st.markdown("---")
        st.caption("v41.0 Enterprise Fixed")
    
    s = RATES[lang]["s"]
    r = RATES[lang]["r"]

    try:
        book = get_data()
        sheet = book.sheet1
        df = pd.DataFrame(sheet.get_all_records())
    except: st.error("DB Error"); st.stop()

    if not df.empty:
        for col in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else: df[col] = 0.0
        empresas = sorted(list(set(df['Empresa'].astype(str))))
        prods_db = sorted(list(set(df['Producto'].astype(str))))
    else: empresas, prods_db = [], []
    
    productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_db)))

    # --- TIEMPO ---
    ahora = datetime.now()
    mes_ui_dict = MONTHS_UI[lang]
    mes_actual_nombre = mes_ui_dict[ahora.month]
    periodo_clave = ahora.strftime("%Y-%m")

    # --- SIDEBAR: META & EXCEL ---
    with st.sidebar:
        st.subheader(f"{t['goal_text']} ({mes_actual_nombre})")
        db_goal = get_monthly_goal_from_db(book, periodo_clave)
        meta_input = st.number_input(f"{t['goal_label']} ({s})", value=db_goal, step=1000.0)
        
        if st.button(t['goal_save'], type="primary"):
            log_action(book, "META_UPDATE", f"{periodo_clave}|{meta_input}")
            st.success("OK!")
            time.sleep(1); st.rerun()

        val_mes_curr = 0
        kg_mes = 0
        if not df.empty:
            df['Fecha_DT'] = pd.to_datetime(df['Fecha_Registro'], errors='coerce')
            df_mes = df[df['Fecha_DT'].dt.to_period('M') == periodo_clave]
            val_mes_curr = df_mes['Valor_BRL'].sum() * r
            kg_mes = df_mes['Kg'].sum()

        if meta_input > 0:
            prog = min(val_mes_curr / meta_input, 1.0)
            st.progress(prog)
            st.caption(f"{prog*100:.1f}% ({s} {val_mes_curr:,.0f} / {s} {meta_input:,.0f})")
        
        st.divider()
        # EXCEL BUTTON
        if not df.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button(t['download_label'], data=buffer, file_name="Data.xlsx", mime='application/vnd.ms-excel')
        
        st.write("")
        if st.button(t['logout_label'], type="secondary"):
            st.session_state.authenticated = False; st.rerun()

    tab_dash, tab_add, tab_admin, tab_log = st.tabs(t['tabs'])

    # 1️⃣ DASHBOARD (+ STOCK ALERT)
    with tab_dash:
        st.title(t['headers'][0])
        if not df.empty:
            val_total = df['Valor_BRL'].sum() * r
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {val_total:,.0f}")
            k2.metric(t['metrics'][1], f"{df['Kg'].sum():,.0f} kg")
            k3.metric(t['metrics'][2], f"{s} {(df['Valor_BRL'].sum()*0.02*r):,.0f}")
            
            st.divider()
            
            # --- SECCIÓN: STOCK ALERT 📦 ---
            st.subheader(t['stock_title'])
            st.caption(t['stock_desc'])
            
            # Calculamos ventas totales por producto
            stock_v = df.groupby('Producto')['Kg'].sum().sort_values(ascending=False).head(5)
            
            for prod_name, sold_kg in stock_v.items():
                LIMIT_KG = 1000.0 # Límite teórico para el gráfico
                pct = min(sold_kg / LIMIT_KG, 1.0)
                
                c_st1, c_st2 = st.columns([3, 1])
                c_st1.progress(pct, text=f"{prod_name}: {sold_kg:,.0f} kg vendidos")
                if pct >= 0.8:
                    c_st2.error("⚠️ Stock Bajo?")
                else:
                    c_st2.success("✅ OK")
            
            st.divider()
            # Tabla Profesional
            st.subheader(t['table_title'])
            df_show = df.copy()
            df_show['Mes'] = df_show['Fecha_DT'].dt.month.map(mes_ui_dict)
            cols = ['Mes', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']
            
            st.dataframe(
                df_show[cols].iloc[::-1], use_container_width=True, hide_index=True,
                column_config={
                    "Valor_BRL": st.column_config.NumberColumn(t['dash_cols']['val'], format=f"{s} %.2f"),
                    "Comissao_BRL": st.column_config.NumberColumn(t['dash_cols']['com'], format=f"{s} %.2f"),
                    "Kg": st.column_config.NumberColumn(t['dash_cols']['kg'], format="%.1f kg")
                }
            )

    # 2️⃣ VENDER (+ PDF)
    with tab_add:
        st.header(t['headers'][1])
        with st.container(border=True):
            c1, c2 = st.columns(2)
            
            # Opción para crear nuevo
            opcion_nuevo = t['actions'][3] # "✨ Novo..."

            sel_emp = c1.selectbox(t['forms'][0], [opcion_nuevo] + empresas)
            # AQUÍ ES DONDE ANTES FALLABA (AHORA YA EXISTE t['new_labels'])
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == opcion_nuevo else sel_emp
            
            sel_prod = c2.selectbox(t['forms'][1], [opcion_nuevo] + productos)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == opcion_nuevo else sel_prod
            
            kg = c1.number_input(t['forms'][2], step=10.0)
            val = c2.number_input(t['forms'][3], step=100.0)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button(t['forms'][4], type="primary"):
                if emp and prod:
                    mes_db = MESES_PT[datetime.now().month]
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mes_db]
                    sheet.append_row(row)
                    log_action(book, "NEW", f"{emp} | {kg}kg | {s} {val:,.2f}")
                    
                    st.success(t['msgs'][0])
                    
                    # --- BOTÓN DE PDF (PROTEGIDO) ---
                    if PDF_AVAILABLE:
                        try:
                            pdf_bytes = create_pdf(emp, prod, kg, val, st.session_state.username)
                            st.download_button(label=t['pdf_btn'], data=pdf_bytes, file_name=f"Recibo_{emp}.pdf", mime='application/pdf')
                        except: st.warning("PDF Error")
                    
                    time.sleep(5) 
                    st.rerun()

    # 3️⃣ ADMIN
    with tab_admin:
        st.header(t['headers'][2])
        filtro = st.text_input("🔍 " + t['actions'][2])
        if not df.empty:
            df_s = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df.tail(10).iloc[::-1]
            for i, r in df_s.iterrows():
                with st.expander(f"📌 {r['Empresa']} | {r['Producto']}"):
                    if st.button(t['actions'][1], key=f"del{i}"):
                        cell = sheet.find(str(r['Fecha_Registro']))
                        sheet.delete_rows(cell.row)
                        log_action(book, "BORRAR", f"{r['Empresa']}")
                        st.success("Deleted!"); time.sleep(1); st.rerun()

    # 4️⃣ HISTORIAL
    with tab_log:
        st.title(t['headers'][3])
        try:
            h_dt = pd.DataFrame(book.worksheet("Historial").get_all_records())
            st.dataframe(h_dt.iloc[::-1], use_container_width=True)
        except: st.write("No logs.")

if __name__ == "__main__":
    main()
