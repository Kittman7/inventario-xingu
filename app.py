import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ESTILO MÓVIL ---
st.set_page_config(page_title="Xingu App", page_icon="🍇", layout="centered")

# Inyectamos CSS para que parezca una App nativa
st.markdown("""
    <style>
    /* Ocultar menú de hamburguesa y footer de Streamlit para look limpio */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Botones más grandes para dedos */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    
    /* Tarjetas de datos (Cards) */
    .st-emotion-cache-1r6slb0 {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Títulos centrados */
    h1, h2, h3 {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. DICCIONARIO DE IDIOMAS ---
TR = {
    "Português": {
        "tab_dash": "📊 Painel",
        "tab_add": "➕ Nova Venda",
        "tab_admin": "🛠️ Editar",
        "search_ph": "🔍 Buscar cliente...",
        "total_val": "Total",
        "total_kg": "Kg",
        "sales_count": "Vendas",
        "form_emp": "Cliente / Empresa",
        "form_prod": "Produto",
        "btn_save": "💾 SALVAR",
        "btn_update": "🔄 ATUALIZAR",
        "btn_delete": "🗑️ APAGAR",
        "msg_success": "✅ Sucesso!",
        "opt_new": "✍️ Novo...",
        "lbl_new": "Digite o nome:",
        "card_val": "Valor:",
        "card_kg": "Qtd:",
        "no_data": "Sem dados recentes"
    },
    "Español": {
        "tab_dash": "📊 Panel",
        "tab_add": "➕ Vender",
        "tab_admin": "🛠️ Editar",
        "search_ph": "🔍 Buscar cliente...",
        "total_val": "Total",
        "total_kg": "Kg",
        "sales_count": "Ventas",
        "form_emp": "Cliente / Empresa",
        "form_prod": "Producto",
        "btn_save": "💾 GUARDAR",
        "btn_update": "🔄 ACTUALIZAR",
        "btn_delete": "🗑️ BORRAR",
        "msg_success": "✅ ¡Listo!",
        "opt_new": "✍️ Nuevo...",
        "lbl_new": "Escribe el nombre:",
        "card_val": "Valor:",
        "card_kg": "Cant:",
        "no_data": "Sin datos recientes"
    },
    "English": {
        "tab_dash": "📊 Dash",
        "tab_add": "➕ Sale",
        "tab_admin": "🛠️ Edit",
        "search_ph": "🔍 Search client...",
        "total_val": "Total",
        "total_kg": "Kg",
        "sales_count": "Sales",
        "form_emp": "Client / Company",
        "form_prod": "Product",
        "btn_save": "💾 SAVE",
        "btn_update": "🔄 UPDATE",
        "btn_delete": "🗑️ DELETE",
        "msg_success": "✅ Done!",
        "opt_new": "✍️ New...",
        "lbl_new": "Type name:",
        "card_val": "Value:",
        "card_kg": "Qty:",
        "no_data": "No recent data"
    }
}

RATES = {
    "Português": {"symbol": "R$", "rate": 1.0},
    "Español":   {"symbol": "$", "rate": 165.0},
    "English":   {"symbol": "USD", "rate": 0.18}
}

# --- 2. CONEXIÓN ---
def get_google_services():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["google_credentials"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    book = client.open("Inventario_Xingu_DB")
    return book

def registrar_historial(book, accion, detalles):
    try:
        sheet_log = book.worksheet("Historial")
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_log.append_row([hora, accion, detalles])
    except:
        pass

# --- 3. APP PRINCIPAL ---
def main():
    # Idioma discreto en el sidebar (para no estorbar)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        lang = st.selectbox("Idioma", ["Español", "Português", "English"])
        st.info("Xingu Cloud v4.0 Mobile")
    
    t = TR[lang]
    rate = RATES[lang]["rate"]
    symbol = RATES[lang]["symbol"]

    # Conexión
    try:
        book = get_google_services()
        sheet = book.sheet1
        raw_data = sheet.get_all_records()
        df = pd.DataFrame(raw_data)
    except:
        st.error("Error de conexión / Conexão")
        st.stop()

    # Listas inteligentes
    if not df.empty:
        lista_empresas_db = sorted(list(set(df['Empresa'].astype(str).tolist())))
        lista_productos_db = sorted(list(set(df['Producto'].astype(str).tolist())))
    else:
        lista_empresas_db, lista_productos_db = [], []

    prods_final = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + lista_productos_db)))

    # --- NAVEGACIÓN TIPO APP (TABS) ---
    # Usamos Tabs arriba para cambiar rápido con el dedo
    tab_add, tab_dash, tab_admin = st.tabs([t['tab_add'], t['tab_dash'], t['tab_admin']])

    # ==========================================
    # 📱 PESTAÑA 1: VENDER (Prioridad #1)
    # ==========================================
    with tab_add:
        st.markdown("### 🍇 Nueva Venta")
        with st.container(border=True): # Tarjeta contenedora
            
            # Cliente
            opc_emp = [t['opt_new']] + lista_empresas_db
            sel_emp = st.selectbox(t['form_emp'], opc_emp, key="sel_emp_add")
            final_emp = st.text_input(t['lbl_new'], key="new_emp_add") if sel_emp == t['opt_new'] else sel_emp

            # Producto
            opc_prod = [t['opt_new']] + prods_final
            sel_prod = st.selectbox(t['form_prod'], opc_prod, key="sel_prod_add")
            final_prod = st.text_input(t['lbl_new'], key="new_prod_add") if sel_prod == t['opt_new'] else sel_prod

            # Datos numéricos (usamos columnas para ahorrar espacio vertical)
            c1, c2 = st.columns(2)
            kg = c1.number_input("Kg", min_value=0.0, step=10.0, key="kg_add")
            val_brl = c2.number_input("R$ (Reais)", min_value=0.0, step=50.0, key="val_add")

            # Botón Gigante
            st.markdown("<br>", unsafe_allow_html=True) # Espacio
            if st.button(t['btn_save'], type="primary"):
                if final_emp and final_prod:
                    row = [final_emp, final_prod, kg, val_brl, val_brl * 0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    registrar_historial(book, "NEW", f"{final_emp} - {kg}kg")
                    st.success(t['msg_success'])
                    st.balloons()
                    st.rerun() # Recarga rápida
                else:
                    st.warning("⚠️ Faltan datos / Dados faltando")

    # ==========================================
    # 📊 PESTAÑA 2: DASHBOARD
    # ==========================================
    with tab_dash:
        if not df.empty:
            # Procesar datos
            df['Valor_BRL'] = pd.to_numeric(df['Valor_BRL'], errors='coerce').fillna(0)
            df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce').fillna(0)
            df['Valor_View'] = df['Valor_BRL'] * rate

            # Tarjetas de Totales (Estilo Métricas Grandes)
            c1, c2, c3 = st.columns(3)
            c1.metric(t['total_val'], f"{symbol} {df['Valor_View'].sum():,.0f}")
            c2.metric(t['total_kg'], f"{df['Kg'].sum():,.0f}")
            c3.metric(t['sales_count'], len(df))

            st.divider()

            # Gráfico limpio para móvil
            fig = px.bar(df, x='Empresa', y='Valor_View', color='Producto', title="")
            fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0)) # Maximizar espacio
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(t['no_data'])

    # ==========================================
    # 🛠️ PESTAÑA 3: ADMINISTRAR (Estilo Tarjetas)
    # ==========================================
    with tab_admin:
        st.markdown("### 🔎 Buscar & Editar")
        filtro = st.text_input("", placeholder=t['search_ph'])
        
        if not df.empty:
            # Filtrar
            if filtro:
                df_show = df[df['Empresa'].str.contains(filtro, case=False, na=False)]
            else:
                df_show = df.tail(10).iloc[::-1] # Mostrar solo las últimas 10 si no hay búsqueda

            # BUCLE PARA GENERAR TARJETAS (NO TABLA)
            # Esto se ve hermoso en celular
            for i, row in df_show.iterrows():
                with st.expander(f"📍 {row['Empresa']} | {row['Producto']}"):
                    # Formulario de edición dentro de la tarjeta
                    with st.form(key=f"edit_{i}"):
                        new_emp = st.text_input("Cliente", value=row['Empresa'])
                        c_k, c_v = st.columns(2)
                        new_kg = c_k.number_input("Kg", value=float(row['Kg']))
                        new_val = c_v.number_input("R$", value=float(row['Valor_BRL']))
                        
                        col_up, col_del = st.columns(2)
                        if col_up.form_submit_button(t['btn_update']):
                            # Fila real en excel es indice + 2
                            # Nota: Esto funciona mejor si buscamos por ID, pero por ahora usaremos lógica simple
                            # Para producción real, mejor buscar la fila exacta. Aquí asumimos orden.
                            # BUSCAR FILA REAL EN EL EXCEL ORIGINAL (IMPORTANTE)
                            fila_real = df[df['Fecha_Registro'] == row['Fecha_Registro']].index[0] + 2
                            
                            sheet.update_cell(fila_real, 1, new_emp)
                            sheet.update_cell(fila_real, 3, new_kg)
                            sheet.update_cell(fila_real, 4, new_val)
                            sheet.update_cell(fila_real, 5, new_val * 0.02)
                            registrar_historial(book, "UPDATE", f"{new_emp}")
                            st.success(t['msg_success'])
                            st.rerun()

                        if col_del.form_submit_button(t['btn_delete'], type="primary"):
                             fila_real = df[df['Fecha_Registro'] == row['Fecha_Registro']].index[0] + 2
                             sheet.delete_rows(fila_real)
                             registrar_historial(book, "DELETE", f"{row['Empresa']}")
                             st.rerun()
        else:
            st.info(t['no_data'])

if __name__ == "__main__":
    main()
