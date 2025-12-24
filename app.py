import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xingu Enterprise", page_icon="🍇", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #0E1117;
        border-radius: 5px;
        padding: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 3px solid #FF4B4B;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<h1 style='text-align: center;'>🔒 Xingu Cloud Access</h1>", unsafe_allow_html=True)
        st.write("")
        password = st.text_input("Senha / Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            try:
                if password == st.secrets["passwords"]["admin_password"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("🚫 Incorrecto / Incorreto")
            except:
                st.error("⚠️ Error: Configura [passwords] en Secrets.")
    return False

# --- IDIOMAS ---
TR = {
    "Português": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gerir", "📜 Histórico"],
        "headers": ["Visão Geral & Tendências", "Nova Venda", "Administração", "Histórico de Atividades"],
        "metrics": ["Valor Total", "Quantidade (Kg)", "Comissão (2%)"],
        "charts": ["Evolução de Vendas (Diária)", "Mix de Produtos", "Vendas por Empresa"],
        "table_title": "Detalhe",
        "forms": ["Cliente / Empresa", "Produto", "Quantidade (Kg)", "Valor (R$)", "Salvar Venda"],
        "actions": ["Atualizar", "APAGAR", "Buscar...", "Novo...", "Apagar Selecionados"],
        "bulk_label": "🗑️ Apagar Vários (Seleção Múltipla)",
        "clean_hist_label": "🗑️ Limpar Histórico",
        "download_label": "📥 Baixar Excel (Mobile Friendly)",
        "logout_label": "🔒 Sair / Cerrar Sesión",
        "msgs": ["Sucesso!", "Dados apagados!", "Sem dados", "Selecione itens"],
        "new_labels": ["Nome do Cliente:", "Nome do Produto:"],
        "col_map": {"Fecha_Hora": "📅 Data/Hora", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "dash_cols": {"emp": "Empresa", "prod": "Produto", "kg": "Quantidade (Kg)", "val": "Valor", "com": "Comissão"},
        "val_map": {"NEW": "🆕 Novo", "VENTA": "💰 Venda", "EDITAR": "✏️ Edição", "BORRAR": "🗑️ Apagado", "BORRADO_MASIVO": "🔥 Apagar Vários", "CREAR": "✨ Criar", "HIST_DEL": "🧹 Limpeza"}
    },
    "Español": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gestionar", "📜 Historial"],
        "headers": ["Visión General & Tendencias", "Nueva Venta", "Administración", "Historial de Actividades"],
        "metrics": ["Valor Total", "Cantidad (Kg)", "Comisión (2%)"],
        "charts": ["Evolución de Ventas (Diaria)", "Mix de Productos", "Ventas por Empresa"],
        "table_title": "Detalle",
        "forms": ["Cliente / Empresa", "Producto", "Cantidad (Kg)", "Valor (R$)", "Guardar Venta"],
        "actions": ["Actualizar", "BORRAR", "Buscar...", "Nuevo...", "Borrar Seleccionados"],
        "bulk_label": "🗑️ Borrado Masivo (Selección Múltiple)",
        "clean_hist_label": "🗑️ Limpiar Historial",
        "download_label": "📥 Descargar Excel (Mobile Friendly)",
        "logout_label": "🔒 Cerrar Sesión / Sair",
        "msgs": ["¡Éxito!", "¡Datos borrados!", "Sin datos", "Selecciona ítems"],
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "col_map": {"Fecha_Hora": "📅 Fecha/Hora", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "dash_cols": {"emp": "Empresa", "prod": "Producto", "kg": "Cantidad (Kg)", "val": "Valor", "com": "Comisión"},
        "val_map": {"NEW": "🆕 Nuevo", "VENTA": "💰 Venta", "EDITAR": "✏️ Edición", "BORRAR": "🗑️ Borrado", "BORRADO_MASIVO": "🔥 Borrado Masivo", "CREAR": "✨ Crear", "HIST_DEL": "🧹 Limpieza"}
    },
    "English": {
        "tabs": ["📊 Dashboard", "➕ New Sale", "🛠️ Manage", "📜 History"],
        "headers": ["Overview & Trends", "New Sale", "Administration", "Activity History"],
        "metrics": ["Total Value", "Quantity (Kg)", "Commission (2%)"],
        "charts": ["Sales Evolution (Daily)", "Product Mix", "Sales by Company"],
        "table_title": "Details",
        "forms": ["Client / Company", "Product", "Quantity (Kg)", "Value (R$)", "Save Sale"],
        "actions": ["Update", "DELETE", "Search...", "New...", "Delete Selected"],
        "bulk_label": "🗑️ Bulk Delete (Multi-Select)",
        "clean_hist_label": "🗑️ Clear History",
        "download_label": "📥 Download Excel (Mobile Friendly)",
        "logout_label": "🔒 Log Out",
        "msgs": ["Success!", "Data deleted!", "No data", "Select items"],
        "new_labels": ["Client Name:", "Product Name:"],
        "col_map": {"Fecha_Hora": "📅 Date/Time", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "dash_cols": {"emp": "Company", "prod": "Product", "kg": "Quantity (Kg)", "val": "Value", "com": "Commission"},
        "val_map": {"NEW": "🆕 New", "VENTA": "💰 Sale", "EDITAR": "✏️ Edit", "BORRAR": "🗑️ Deleted", "BORRADO_MASIVO": "🔥 Bulk", "CREAR": "✨ Create", "HIST_DEL": "🧹 Clean"}
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

# --- APP PRINCIPAL ---
def main():
    if not check_password():
        return

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
        lang = st.selectbox("Language / Idioma", ["Español", "Português", "English"])
        st.caption("v17.0 Mobile Excel")
    
    t = TR[lang]
    s = RATES[lang]["s"]
    r = RATES[lang]["r"]

    try:
        book = get_data()
        sheet = book.sheet1
        df = pd.DataFrame(sheet.get_all_records())
    except:
        st.error("Conectando...")
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

    # --- SIDEBAR: EXCEL PRO ---
    with st.sidebar:
        st.divider()
        if not df.empty:
            buffer = io.BytesIO()
            df_export = df.copy()
            df_export['Fecha_Temp'] = pd.to_datetime(df_export['Fecha_Registro'], errors='coerce')
            
            meses_pt = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_export['Periodo'] = df_export['Fecha_Temp'].dt.to_period('M')
                periodos = sorted(df_export['Periodo'].unique(), reverse=True)
                
                for periodo in periodos:
                    data_mes = df_export[df_export['Periodo'] == periodo].copy()
                    
                    data_mes['Fecha'] = data_mes['Fecha_Temp'].dt.strftime('%d/%m/%Y')
                    data_mes['Hora'] = data_mes['Fecha_Temp'].dt.strftime('%H:%M')
                    
                    cols = ['Fecha', 'Hora', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']
                    data_final = data_mes[[c for c in cols if c in data_mes.columns]]
                    
                    nombre_pestana = f"{meses_pt[periodo.month]} {periodo.year}"
                    data_final.to_excel(writer, sheet_name=nombre_pestana, index=False)
                    
                    # --- AUTO-AJUSTE DE COLUMNAS ---
                    worksheet = writer.sheets[nombre_pestana]
                    # Ajustamos ancho: A(Fecha)=12, B(Hora)=8, C(Empresa)=20, D(Prod)=20, etc.
                    worksheet.set_column('A:A', 12)
                    worksheet.set_column('B:B', 8)
                    worksheet.set_column('C:D', 20)
                    worksheet.set_column('E:G', 12)
            
            st.download_button(
                label=t['download_label'],
                data=buffer,
                file_name=f'Relatorio_Xingu_{datetime.now().strftime("%Y-%m")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.write("")
        if st.button(t['logout_label'], type="secondary"):
            st.session_state.password_correct = False
            st.rerun()

    tab_dash, tab_add, tab_admin, tab_log = st.tabs(t['tabs'])

    with tab_dash:
        st.title(t['headers'][0])
        if not df.empty:
            val_total = df['Valor_BRL'].sum() * r
            kg_total = df['Kg'].sum()
            com_total = (df['Valor_BRL'].sum() * 0.02) * r
            
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {val_total:,.0f}")
            k2.metric(t['metrics'][1], f"{kg_total:,.0f}")
            k3.metric(t['metrics'][2], f"{s} {com_total:,.0f}")
            
            st.divider()

            df['Fecha_DT'] = pd.to_datetime(df['Fecha_Registro'], errors='coerce')
            df['Fecha_Dia'] = df['Fecha_DT'].dt.date
            df['Valor_View'] = df['Valor_BRL'] * r
            df_trend = df.groupby('Fecha_Dia')['Valor_View'].sum().reset_index()
            
            st.subheader(t['charts'][0])
            fig_line = px.line(df_trend, x='Fecha_Dia', y='Valor_View', markers=True)
            fig_line.update_layout(xaxis_title="", yaxis_title=s, height=300)
            fig_line.update_traces(line_color='#FF4B4B', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            c_izq, c_der = st.columns([1, 2])
            with c_izq:
                st.subheader(t['charts'][1])
                fig_pie = px.pie(df, names='Producto', values='Kg', hole=0.5)
                fig_pie.update_layout(legend=dict(orientation="v"), margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            with c_der:
                st.subheader(t['table_title'])
                df_table = df.copy()
                df_table['Val_Show'] = df_table['Valor_BRL'] * r
                df_table['Com_Show'] = (df_table['Valor_BRL'] * 0.02) * r
                cols = ['Empresa', 'Producto', 'Kg', 'Val_Show', 'Com_Show']
                df_table = df_table[cols].rename(columns={
                    'Empresa': t['dash_cols']['emp'], 'Producto': t['dash_cols']['prod'],
                    'Kg': t['dash_cols']['kg'], 'Val_Show': f"{t['dash_cols']['val']} ({s})",
                    'Com_Show': f"{t['dash_cols']['com']} ({s})"
                })
                st.dataframe(df_table.iloc[::-1], use_container_width=True, height=350)
        else:
            st.info(t['msgs'][2])

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
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    log_action(book, "NEW", f"{emp} | {kg}kg")
                    st.success(t['msgs'][0])
                    st.rerun()

    with tab_admin:
        st.header(t['headers'][2])
        with st.expander(t['bulk_label'], expanded=False):
            if not df.empty:
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
                        p = st.progress(0)
                        for idx, rw in enumerate(rows):
                            sheet.delete_rows(rw)
                            p.progress((idx + 1)/len(rows))
                        log_action(book, "BORRADO_MASIVO", f"{len(rows)}")
                        st.success(t['msgs'][1])
                        time.sleep(1)
                        st.rerun()
            else: st.info(t['msgs'][2])
        st.divider()
        filt = st.text_input("🔍", placeholder=t['actions'][2], label_visibility="collapsed")
        if not df.empty:
            d_show = df[df['Empresa'].str.contains(filt, case=False)] if filt else df.tail(10).iloc[::-1]
            for i, r in d_show.iterrows():
                with st.expander(f"✏️ {r['Empresa']} - {r['Producto']}"):
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
                            st.rerun()

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
            else: st.info("Log vacío")
        except: st.warning("Falta Hoja Historial")

if __name__ == "__main__":
    main()
