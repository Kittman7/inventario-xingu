import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xingu Admin", page_icon="🍇", layout="wide")

# --- ESTILO CSS PROFESIONAL (Basado en tu imagen) ---
st.markdown("""
    <style>
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tarjetas de Métricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
    }
    div[data-testid="stMetricLabel"] {
        color: #B0B0B0; /* Gris claro */
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF; /* Blanco brillante */
        font-weight: bold;
    }
    
    /* Pestañas grandes */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0E1117;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 2px solid #FF4B4B;
    }
    
    /* Botones gruesos para móvil */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. IDIOMAS ---
TR = {
    "Português": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gerir/Apagar", "📜 Histórico"],
        "metrics": ["Valor Total", "Quantidade (Kg)", "Comissão (2%)"],
        "charts": ["Mix de Produtos", "Vendas por Empresa"],
        "forms": ["Cliente / Empresa", "Produto", "Quantidade (Kg)", "Valor (R$)", "Salvar Venda"],
        "actions": ["Atualizar", "APAGAR DADOS", "Buscar cliente...", "Novo..."],
        "msgs": ["Sucesso!", "Tem certeza?", "Sem dados", "Histórico de Atividades"],
        "new_labels": ["Digite o nome:", "Digite o produto:"]
    },
    "Español": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Gestionar/Borrar", "📜 Historial"],
        "metrics": ["Valor Total", "Cantidad (Kg)", "Comisión (2%)"],
        "charts": ["Mix de Productos", "Ventas por Empresa"],
        "forms": ["Cliente / Empresa", "Producto", "Cantidad (Kg)", "Valor (R$)", "Guardar Venta"],
        "actions": ["Actualizar", "BORRAR DATOS", "Buscar cliente...", "Nuevo..."],
        "msgs": ["¡Éxito!", "¿Seguro?", "Sin datos", "Historial de Actividades"],
        "new_labels": ["Escribe el nombre:", "Escribe el producto:"]
    },
    "English": {
        "tabs": ["📊 Dashboard", "➕ New Sale", "🛠️ Manage/Delete", "📜 History"],
        "metrics": ["Total Value", "Quantity (Kg)", "Commission (2%)"],
        "charts": ["Product Mix", "Sales by Company"],
        "forms": ["Client / Company", "Product", "Quantity (Kg)", "Value (R$)", "Save Sale"],
        "actions": ["Update", "DELETE DATA", "Search client...", "New..."],
        "msgs": ["Success!", "Are you sure?", "No data", "Activity Log"],
        "new_labels": ["Type name:", "Type product:"]
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
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, detail])
    except: pass

# --- 3. APP PRINCIPAL ---
def main():
    # Sidebar minimalista
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
        lang = st.selectbox("Language", ["Español", "Português", "English"])
        st.write("---")
        st.caption("v5.0 Ultimate")

    t = TR[lang]
    s = RATES[lang]["s"]
    r = RATES[lang]["r"]

    # Cargar datos
    try:
        book = get_data()
        sheet = book.sheet1
        df = pd.DataFrame(sheet.get_all_records())
    except:
        st.error("Conectando...")
        st.stop()

    # Preparar listas
    if not df.empty:
        # Asegurar tipos numéricos
        for col in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0 # Crear columna si no existe

        empresas = sorted(list(set(df['Empresa'].astype(str))))
        prods_db = sorted(list(set(df['Producto'].astype(str))))
    else:
        empresas, prods_db = [], []

    productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + prods_db)))

    # --- PESTAÑAS PRINCIPALES ---
    tab_dash, tab_add, tab_admin, tab_log = st.tabs(t['tabs'])

    # 1️⃣ DASHBOARD (Estilo Visual)
    with tab_dash:
        if not df.empty:
            # Cálculos
            val_total = df['Valor_BRL'].sum() * r
            kg_total = df['Kg'].sum()
            com_total = (df['Valor_BRL'].sum() * 0.02) * r # Comisión 2%
            
            # 3 KPIs GRANDES
            k1, k2, k3 = st.columns(3)
            k1.metric(t['metrics'][0], f"{s} {val_total:,.0f}")
            k2.metric(t['metrics'][1], f"{kg_total:,.0f}")
            k3.metric(t['metrics'][2], f"{s} {com_total:,.0f}")
            
            st.divider()
            
            # GRÁFICOS (Pie + Barras)
            g1, g2 = st.columns([1, 2])
            
            with g1:
                st.subheader(t['charts'][0]) # Mix Productos
                fig_pie = px.pie(df, names='Producto', values='Kg', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with g2:
                st.subheader(t['charts'][1]) # Ventas Empresa
                # Agrupar datos para gráfico limpio
                df_chart = df.copy()
                df_chart['Valor_View'] = df_chart['Valor_BRL'] * r
                fig_bar = px.bar(df_chart, x='Empresa', y='Valor_View', color='Producto')
                fig_bar.update_layout(xaxis_title="", yaxis_title=s)
                st.plotly_chart(fig_bar, use_container_width=True)

        else:
            st.info(t['msgs'][2])

    # 2️⃣ VENDER (Rápido)
    with tab_add:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            
            # Selectores con opción "Nuevo"
            sel_emp = c1.selectbox(t['forms'][0], [t['actions'][3]] + empresas)
            emp = c1.text_input(t['new_labels'][0]) if sel_emp == t['actions'][3] else sel_emp
            
            sel_prod = c2.selectbox(t['forms'][1], [t['actions'][3]] + productos)
            prod = c2.text_input(t['new_labels'][1]) if sel_prod == t['actions'][3] else sel_prod
            
            kg = c1.number_input(t['forms'][2], step=10.0)
            val = c2.number_input(t['forms'][3], step=100.0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['forms'][4], type="primary", use_container_width=True):
                if emp and prod:
                    # Guardar con comisión calculada
                    row = [emp, prod, kg, val, val*0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    log_action(book, "VENTA", f"{emp} | {kg}kg | {s}{val*r}")
                    st.success(t['msgs'][0])
                    st.rerun()

    # 3️⃣ GESTIONAR Y BORRAR
    with tab_admin:
        filtro = st.text_input("🔍", placeholder=t['actions'][2])
        if not df.empty:
            df_show = df[df['Empresa'].str.contains(filtro, case=False)] if filtro else df.tail(10).iloc[::-1]
            
            for i, row in df_show.iterrows():
                with st.expander(f"{row['Empresa']} - {row['Producto']} ({row['Fecha_Registro']})"):
                    c_a, c_b = st.columns(2)
                    new_kg = c_a.number_input("Kg", value=float(row['Kg']), key=f"k_{i}")
                    new_val = c_b.number_input("R$", value=float(row['Valor_BRL']), key=f"v_{i}")
                    
                    b1, b2 = st.columns(2)
                    if b1.button(t['actions'][0], key=f"up_{i}"): # Actualizar
                        # Buscar fila real (truco simple: coincidencia de fecha)
                        cell = sheet.find(row['Fecha_Registro'])
                        if cell:
                            r_idx = cell.row
                            sheet.update_cell(r_idx, 3, new_kg)
                            sheet.update_cell(r_idx, 4, new_val)
                            sheet.update_cell(r_idx, 5, new_val * 0.02)
                            log_action(book, "EDITAR", f"Fila {r_idx}")
                            st.rerun()
                            
                    if b2.button(t['actions'][1], key=f"del_{i}", type="primary"): # BORRAR
                        cell = sheet.find(row['Fecha_Registro'])
                        if cell:
                            sheet.delete_rows(cell.row)
                            log_action(book, "BORRAR", f"{row['Empresa']} - {row['Producto']}")
                            st.warning(t['msgs'][0])
                            st.rerun()

    # 4️⃣ HISTORIAL
    with tab_log:
        st.subheader(t['msgs'][3])
        try:
            h_data = book.worksheet("Historial").get_all_records()
            st.dataframe(pd.DataFrame(h_data).iloc[::-1], use_container_width=True)
        except:
            st.warning("Crea la hoja 'Historial' en Google Sheets (Cols: Fecha, Accion, Detalle)")

if __name__ == "__main__":
    main()
