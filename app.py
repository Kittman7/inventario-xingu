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

# --- LOGIN SIMPLE (CON FORMULARIO PARA GUARDAR CLAVE) ---
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
        
        # Formulario para que el navegador guarde la contraseña
        with st.form("login_form"):
            input_pass = st.text_input("Senha / Contraseña", type="password")
            submit_btn = st.form_submit_button("Entrar", type="primary")
        
        if submit_btn:
            # .strip() elimina espacios accidentales
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
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nova Venda", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venda", "Gestão", "Auditoria"],
        "metrics": ["Faturamento Total", "Volume (Kg)", "Comissão (2%)", "Ticket Médio", "Melhor Cliente"],
        "charts": ["Tendência", "Mix Produtos", "Por Empresa"],
        "table_title": "Detalhes",
        "forms": ["Cliente", "Produto", "Kg", "Valor (R$)", "✅ Confirmar"],
        "actions": ["Salvar", "DELETAR", "Buscar...", "✨ Novo...", "🗑️ Apagar Seleção"],
        "bulk_label": "Gestão em Massa (Apagar Vários)",
        "clean_hist_label": "Limpeza de Histórico",
        "dl_excel": "📗 Baixar Excel",
        "logout": "🔒 Sair",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar Meta",
        "msgs": ["Sucesso!", "Apagado!", "Sem dados", "Atualizado!", "Seleccione items"],
        "pdf": "📄 Baixar Recibo",
        "stock_t": "📦 Estoque",
        "new_labels": ["Nome Cliente:", "Nome Produto:"],
        "dash_cols": {"val": "Valor", "com": "Comissão", "kg": "Kg"},
        "install": "📲 Instalar: Menu -> Adicionar à Tela de Início",
        "filter": "📅 Filtrar por Data",
        "col_map": {"Fecha_Hora": "📅 Data", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Massa", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"}
    },
    "Español": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ Nueva Venta", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "Registrar Venta", "Gestión", "Auditoría"],
        "metrics": ["Facturación Total", "Volumen (Kg)", "Comisión (2%)", "Ticket Medio", "Mejor Cliente"],
        "charts": ["Tendencia", "Mix Productos", "Por Empresa"],
        "table_title": "Detalles",
        "forms": ["Cliente", "Producto", "Kg", "Valor ($)", "✅ Confirmar"],
        "actions": ["Guardar", "BORRAR", "Buscar...", "✨ Nuevo...", "🗑️ Borrar Selección"],
        "bulk_label": "Gestión Masiva (Borrar Varios)",
        "clean_hist_label": "Limpieza de Historial",
        "dl_excel": "📗 Bajar Excel",
        "logout": "🔒 Salir",
        "goal_lbl": "🎯 Meta de", "goal_btn": "💾 Salvar Meta",
        "msgs": ["¡Éxito!", "¡Borrado!", "Sin datos", "¡Actualizado!", "Seleccione items"],
        "pdf": "📄 Bajar Recibo",
        "stock_t": "📦 Stock",
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "dash_cols": {"val": "Valor", "com": "Comisión", "kg": "Kg"},
        "install": "📲 Instalar: Menú -> Agregar a Pantalla de Inicio",
        "filter": "📅 Filtrar por Fecha",
        "col_map": {"Fecha_Hora": "📅 Fecha", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Del", "BORRADO_MASIVO": "🔥 Masa", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limp", "META_UPDATE": "🎯 Meta"}
    },
    "English": {
        "tabs": [f"📊 {NOMBRE_EMPRESA}", "➕ New Sale", "🛠️ Admin", "📜 Log"],
        "headers": ["Dashboard", "New Sale", "Admin", "Log"],
        "metrics": ["Total Revenue", "Volume (Kg)", "Commission (2%)", "Avg Ticket", "Top Client"],
        "charts": ["Trend", "Mix", "By Company"],
        "table_title": "Details",
        "forms": ["Client", "Product", "Kg", "Value", "✅ Confirm"],
        "actions": ["Save", "DELETE", "Search...", "✨ New...", "🗑️ Delete Selection"],
        "bulk_label": "Bulk Management",
        "clean_hist_label": "Clear History",
        "dl_excel": "📗 Download Excel",
        "logout": "🔒 Logout",
        "goal_lbl": "🎯 Goal for", "goal_btn": "💾 Save Goal",
        "msgs": ["Success!", "Deleted!", "No data", "Updated!", "Select items"],
        "pdf": "📄 Download Receipt",
        "stock_t": "📦 Stock",
        "new_labels": ["Client Name:", "Product Name:"],
        "dash_cols": {"val": "Value", "com": "Comm", "kg": "Kg"},
        "install": "📲 Install: Menu -> Add to Home Screen",
        "filter": "📅 Filter by Date",
        "col_map": {"Fecha_Hora": "📅 Date", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Deleted", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean", "META_UPDATE": "🎯 Goal"}
    }
}
RATES = { "Português": {"s": "R$", "r": 1.0}, "Español": {"s": "$", "r": 165.0}, "English": {"s": "USD", "r": 0.18} }
MESES_UI = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# --- CONEXIÓN CACHEADA ⚡ ---
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
        st.info(t.get("install", "Install App"))
        st.caption("v48.0 Excel Clásico")
    
    s = RATES[lang]["s"]; r = RATES[lang]["r"]

    try:
        book = get_data(); sheet = book.sheet1; df = pd.DataFrame(sheet.get_all_records())
    except: st.error("DB Error"); st.stop()

    if not df.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df['Empresa'].astype(str))))
        prods_db = sorted(list(set(df['Producto'].astype(str))))
    else: empresas, prods_db = [], []
    
    productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_db)))
    ahora = datetime.now(); periodo_clave = ahora.strftime("%Y-%m")

    # SIDEBAR META
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
        
        # --- EXCEL SIMPLE (COMO ANTES) ---
        if not df.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Solo descargamos los datos tal cual, sin hojas extra ni formatos raros
                df.to_excel(writer, index=False)
            st.download_button(
                label=t['dl_excel'],
                data=buffer, 
                file_name=f"Data_Xingu_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        if st.button(t['logout']): st.session_state.authenticated = False; st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(t['tabs'])

    # 1. DASHBOARD
    with tab1:
        st.title(t['headers'][0])
        if not df.empty:
            with st.expander(t.get("filter", "Filter Date"), expanded=False):
                col_f1, col_f2 = st.columns(2)
                df['Fecha_DT'] = pd.to_datetime(df['Fecha_Registro'], errors='coerce')
                d_min = df['Fecha_DT'].min().date()
                d_max = df['Fecha_DT'].max().date()
                d1 = col_f1.date_input("Start", d_min)
                d2 = col_f2.date_input("End", d_max)
            
            mask = (df['Fecha_DT'].dt.date >= d1) & (df['Fecha_DT'].dt.date <= d2)
            df_fil = df.loc[mask]

            if df_fil.empty:
                st.warning("No Data in Range")
            else:
                k1, k2, k3 = st.columns(3)
                k1.metric(t['metrics'][0], f"{s} {(df_fil['Valor_BRL'].sum() * r):,.0f}")
                k2.metric(t['metrics'][1], f"{df_fil['Kg'].sum():,.0f} kg")
                k3.metric(t['metrics'][2], f"{s} {(df_fil['Valor_BRL'].sum()*0.02*r):,.0f}")
                
                st.divider(); st.subheader(t['stock_t'])
                stock = df_fil.groupby('Producto')['Kg'].sum().sort_values(ascending=False).head(3)
                for p, q in stock.items(): st.progress(min(q/1000, 1.0), text=f"{p}: {q:,.0f} kg")
                
                st.divider()
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

                st.subheader(t['table_title'])
                st.dataframe(
                    df_fil[['Fecha_Registro', 'Empresa', 'Producto', 'Kg', 'Valor_BRL']].iloc[::-1],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Valor_BRL": st.column_config.NumberColumn(t['dash_cols']['val'], format=f"{s} %.2f"),
                        "Kg": st.column_config.NumberColumn(t['dash_cols']['kg'], format="%.1f kg")
                    }
                )

    # 2. VENDER
    with tab2:
        st.header(t['headers'][1])
        with st.container(border=True):
            c1, c2 = st.columns(2)
            op_new = t['actions'][3]
            sel_emp = c1.selectbox(t['forms'][0], [op_new] + empresas)
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == op_new else sel_emp
            sel_prod = c2.selectbox(t['forms'][1], [op_new] + productos)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == op_new else sel_prod
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
                    time.sleep(2); st.rerun()

    # 3. ADMIN
    with tab3:
        filtro = st.text_input(t['actions'][2]) 
        if not df.empty:
            df_s = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)] if filtro else df.tail(5).iloc[::-1]
            for i, r in df_s.iterrows():
                with st.expander(f"{r['Empresa']} | {r['Producto']}"):
                    if st.button(t['actions'][1], key=f"d{i}"):
                        try:
                            cell = sheet.find(str(r['Fecha_Registro']))
                            sheet.delete_rows(cell.row)
                            st.success(t['msgs'][1]); time.sleep(1); st.rerun()
                        except: st.error("Error")
            st.divider()
            with st.expander(t['bulk_label']):
                df_rev = df.iloc[::-1].reset_index()
                opc = [f"{r['Empresa']} | {r['Producto']} | {r['Fecha_Registro']}" for i, r in df_rev.iterrows()]
                sels = st.multiselect(t['msgs'][4], opc)
                if st.button(t['actions'][4], type="primary"):
                    if sels:
                        dates = [x.split(" | ")[-1] for x in sels]
                        rows_to_del = []
                        all_recs = sheet.get_all_records()
                        for i, r in enumerate(all_recs):
                            if str(r['Fecha_Registro']) in dates: rows_to_del.append(i + 2)
                        rows_to_del.sort(reverse=True)
                        for rw in rows_to_del: sheet.delete_rows(rw)
                        log_action(book, "BORRADO_MASIVO", f"{len(rows_to_del)}")
                        st.success(t['msgs'][1]); time.sleep(1); st.rerun()

    # 4. LOG (BONITO)
    with tab4:
        st.title(t['headers'][3])
        try:
            sh_log = book.worksheet("Historial")
            h_dt = pd.DataFrame(sh_log.get_all_records())
            
            if not h_dt.empty:
                show_log = h_dt.copy()
                if "Accion" in show_log.columns:
                    show_log["Accion"] = show_log["Accion"].replace(t['val_map'])
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
            else:
                st.info(t['msgs'][2])
        except: st.write("Log vacío")

if __name__ == "__main__":
    main()
