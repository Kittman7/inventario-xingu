import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xingu Admin", page_icon="🍇", layout="wide")

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

# --- 1. DICCIONARIO DE IDIOMAS ---
TR = {
    "Português": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gerir", "📜 Histórico"],
        "headers": ["Gestão de Vendas", "Nova Venda", "Administração", "Histórico de Atividades"],
        "metrics": ["Valor Total", "Quantidade (Kg)", "Comissão (2%)"],
        "charts": ["Mix de Produtos", "Vendas por Empresa"],
        "forms": ["Cliente / Empresa", "Produto", "Quantidade (Kg)", "Valor (R$)", "Salvar Venda"],
        "actions": ["Atualizar", "APAGAR", "Buscar...", "Novo...", "Apagar Selecionados"],
        "bulk_label": "🗑️ Apagar Vários (Seleção Múltipla)",
        "msgs": ["Sucesso!", "Dados apagados!", "Sem dados", "Selecione itens para apagar"],
        "new_labels": ["Nome do Cliente:", "Nome do Produto:"],
        # TRADUCCIÓN DE LA TABLA
        "col_map": {"Fecha_Hora": "📅 Data/Hora", "Accion": "⚡ Ação", "Detalles": "📝 Detalhes"},
        "val_map": {
            "NEW": "🆕 Novo Registro", 
            "VENTA": "💰 Venda", 
            "EDITAR": "✏️ Edição", 
            "BORRAR": "🗑️ Apagado", 
            "BORRADO_MASIVO": "🔥 Apagar Vários",
            "CREAR": "✨ Criar"
        }
    },
    "Español": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gestionar", "📜 Historial"],
        "headers": ["Gestión de Ventas", "Nueva Venta", "Administración", "Historial de Actividades"],
        "metrics": ["Valor Total", "Cantidad (Kg)", "Comisión (2%)"],
        "charts": ["Mix de Productos", "Ventas por Empresa"],
        "forms": ["Cliente / Empresa", "Producto", "Cantidad (Kg)", "Valor (R$)", "Guardar Venta"],
        "actions": ["Actualizar", "BORRAR", "Buscar...", "Nuevo...", "Borrar Seleccionados"],
        "bulk_label": "🗑️ Borrado Masivo (Selección Múltiple)",
        "msgs": ["¡Éxito!", "¡Datos borrados!", "Sin datos", "Selecciona ítems para borrar"],
        "new_labels": ["Nombre Cliente:", "Nombre Producto:"],
        "col_map": {"Fecha_Hora": "📅 Fecha/Hora", "Accion": "⚡ Acción", "Detalles": "📝 Detalles"},
        "val_map": {
            "NEW": "🆕 Nuevo", 
            "VENTA": "💰 Venta", 
            "EDITAR": "✏️ Edición", 
            "BORRAR": "🗑️ Borrado", 
            "BORRADO_MASIVO": "🔥 Borrado Masivo",
            "CREAR": "✨ Crear"
        }
    },
    "English": {
        "tabs": ["📊 Dashboard", "➕ New Sale", "🛠️ Manage", "📜 History"],
        "headers": ["Sales Management", "New Sale", "Administration", "Activity History"],
        "metrics": ["Total Value", "Quantity (Kg)", "Commission (2%)"],
        "charts": ["Product Mix", "Sales by Company"],
        "forms": ["Client / Company", "Product", "Quantity (Kg)", "Value (R$)", "Save Sale"],
        "actions": ["Update", "DELETE", "Search...", "New...", "Delete Selected"],
        "bulk_label": "🗑️ Bulk Delete (Multi-Select)",
        "msgs": ["Success!", "Data deleted!", "No data", "Select items to delete"],
        "new_labels": ["Client Name:", "Product Name:"],
        "col_map": {"Fecha_Hora": "📅 Date/Time", "Accion": "⚡ Action", "Detalles": "📝 Details"},
        "val_map": {
            "NEW": "🆕 New Record", 
            "VENTA": "💰 Sale", 
            "EDITAR": "✏️ Edit", 
            "BORRAR": "🗑️ Deleted", 
            "BORRADO_MASIVO": "🔥 Bulk Delete",
            "CREAR": "✨ Create"
        }
    }
}

RATES = {
    "Português": {"s": "R$", "r": 1.0},
    "Español":   {"s": "$", "r": 165.0},
    "English":   {"s": "USD", "r": 0.18}
}

# --- 2. CONEXIÓN ---
def get_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = gspread.authorize(creds)
    book = client.open("Inventario_Xingu_DB")
    return book

def log_action(book, action, detail):
    try:
        # Guardamos en la base de datos SIEMPRE en un código estándar (NEW, BORRAR, etc.)
        # Luego lo traducimos solo al mostrarlo.
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, detail])
    except: pass

# --- 3. APP PRINCIPAL ---
def main():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
        lang = st.selectbox("Language / Idioma", ["Español", "Português", "English"])
        st.caption("v7.0 Translation")

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

    # --- PESTAÑAS ---
    tab_dash, tab_add, tab_admin, tab_log = st.tabs(t['tabs'])

    # 1️⃣ DASHBOARD
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
            
            g1, g2 = st.columns([1, 2])
            with g1:
                st.subheader(t['charts'][0])
                fig_pie = px.pie(df, names='Producto', values='Kg', hole=0.5)
                fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                st.subheader(t['charts'][1])
                df_chart = df.copy()
                df_chart['Valor_View'] = df_chart['Valor_BRL'] * r
                fig_bar = px.bar(df_chart, x='Empresa', y='Valor_View', color='Producto')
                fig_bar.update_layout(xaxis_title="", yaxis_title=s)
                st.plotly_chart(fig_bar, use_container_width=True)
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
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    log_action(book, "NEW", f"{emp} | {kg}kg")
                    st.success(t['msgs'][0])
                    st.rerun()

    # 3️⃣ GESTIONAR
    with tab_admin:
        st.header(t['headers'][2])
        with st.expander(t['bulk_label'], expanded=False):
            if not df.empty:
                df_display = df.iloc[::-1].reset_index()
                opciones = [f"{row['Empresa']} | {row['Producto']} | {row['Fecha_Registro']}" for i, row in df_display.iterrows()]
                seleccionados = st.multiselect(t['msgs'][3], opciones)
                
                if st.button(t['actions'][4], type="primary"):
                    if seleccionados:
                        fechas_a_borrar = [s.split(" | ")[-1] for s in seleccionados]
                        filas_a_borrar = []
                        all_records = sheet.get_all_records()
                        for i, record in enumerate(all_records):
                            if str(record['Fecha_Registro']) in fechas_a_borrar:
                                filas_a_borrar.append(i + 2)
                        filas_a_borrar.sort(reverse=True)
                        
                        prog = st.progress(0)
                        for idx, fila in enumerate(filas_a_borrar):
                            sheet.delete_rows(fila)
                            prog.progress((idx + 1) / len(filas_a_borrar))
                        
                        log_action(book, "BORRADO_MASIVO", f"{len(filas_a_borrar)} items")
                        st.success(t['msgs'][1])
                        time.sleep(1)
                        st.rerun()
            else:
                st.info(t['msgs'][2])

        st.divider()
        st.subheader(t['actions'][2]) # "Buscar..."
        filtro = st.text_input("🔍", placeholder=t['actions'][2], label_visibility="collapsed")
        if not df.empty:
            df_show = df[df['Empresa'].str.contains(filtro, case=False)] if filtro else df.tail(10).iloc[::-1]
            for i, row in df_show.iterrows():
                with st.expander(f"✏️ {row['Empresa']} - {row['Producto']}"):
                    c_a, c_b = st.columns(2)
                    new_kg = c_a.number_input("Kg", value=float(row['Kg']), key=f"k_{i}")
                    new_val = c_b.number_input("R$", value=float(row['Valor_BRL']), key=f"v_{i}")
                    
                    if st.button(t['actions'][0], key=f"up_{i}"):
                        cell = sheet.find(str(row['Fecha_Registro']))
                        if cell:
                            sheet.update_cell(cell.row, 3, new_kg)
                            sheet.update_cell(cell.row, 4, new_val)
                            sheet.update_cell(cell.row, 5, new_val * 0.02)
                            log_action(book, "EDITAR", f"{row['Empresa']}")
                            st.rerun()

    # 4️⃣ HISTORIAL (TRADUCIDO)
    with tab_log:
        st.title(t['headers'][3])
        try:
            h_data = book.worksheet("Historial").get_all_records()
            df_log = pd.DataFrame(h_data)
            
            if not df_log.empty:
                # 1. Renombrar Columnas (Fecha_Hora -> Data/Hora)
                df_log = df_log.rename(columns=t['col_map'])
                
                # 2. Traducir los valores de la columna "Accion" / "Ação"
                # Usamos el nombre traducido de la columna para acceder a ella
                col_accion_traducida = t['col_map']["Accion"]
                
                # Reemplazamos los códigos (NEW, BORRAR) por texto bonito (Novo, Apagado)
                df_log[col_accion_traducida] = df_log[col_accion_traducida].replace(t['val_map'])
                
                # Mostrar tabla ordenada
                st.dataframe(df_log.iloc[::-1], use_container_width=True)
            else:
                st.info("Log vacío")
        except:
            st.warning("Crea la hoja 'Historial' en Google Sheets")

if __name__ == "__main__":
    main()
