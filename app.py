import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Xingu Fruit Enterprise", page_icon="🍇", layout="wide")

# --- TASAS DE CAMBIO (Configurables) ---
RATES = {
    "Português": {"symbol": "R$", "rate": 1.0, "locale": "pt_BR"},
    "Español":   {"symbol": "CLP $", "rate": 165.0, "locale": "es_CL"},
    "English":   {"symbol": "USD $", "rate": 0.18, "locale": "en_US"}
}

# --- TEXTOS E IDIOMAS ---
translations = {
    "Português": {
        "menu": "Gestão de Vendas",
        "nav_manage": "Gerenciar",
        "mode_view": "Visualizar",
        "mode_add": "Adicionar Nova",
        "mode_edit": "Editar Existente",
        "mode_del": "Remover",
        "btn_save": "Salvar Alterações",
        "btn_add": "Adicionar Venda",
        "btn_del": "Confirmar Exclusão",
        "log_title": "Histórico de Atividades",
        "col_company": "Empresa",
        "col_product": "Produto",
        "col_qty": "Quantidade (Kg)",
        "col_value": "Valor",
        "col_comm": "Comissão",
        "msg_success": "Operação realizada com sucesso!",
        "log_action": "Ação",
        "log_time": "Data/Hora",
        "log_desc": "Detalhes"
    },
    "Español": {
        "menu": "Gestión de Ventas",
        "nav_manage": "Administrar",
        "mode_view": "Visualizar",
        "mode_add": "Agregar Nueva",
        "mode_edit": "Editar Existente",
        "mode_del": "Eliminar",
        "btn_save": "Guardar Cambios",
        "btn_add": "Agregar Venta",
        "btn_del": "Confirmar Eliminación",
        "log_title": "Historial de Actividad",
        "col_company": "Empresa",
        "col_product": "Producto",
        "col_qty": "Cantidad (Kg)",
        "col_value": "Valor",
        "col_comm": "Comisión",
        "msg_success": "¡Operación exitosa!",
        "log_action": "Acción",
        "log_time": "Fecha/Hora",
        "log_desc": "Detalles"
    },
    "English": {
        "menu": "Sales Management",
        "nav_manage": "Manage",
        "mode_view": "View Only",
        "mode_add": "Add New",
        "mode_edit": "Edit Existing",
        "mode_del": "Delete",
        "btn_save": "Save Changes",
        "btn_add": "Add Sale",
        "btn_del": "Confirm Delete",
        "log_title": "Activity Log",
        "col_company": "Company",
        "col_product": "Product",
        "col_qty": "Qty (Kg)",
        "col_value": "Value",
        "col_comm": "Commission",
        "msg_success": "Operation successful!",
        "log_action": "Action",
        "log_time": "Date/Time",
        "log_desc": "Details"
    }
}

# --- FUNCIÓN: GESTIÓN DE ESTADO (BASE DE DATOS) ---
def init_session():
    # 1. Base de Datos Principal
    if 'df_data' not in st.session_state:
        data = {
            'Empresa': ['EL ROXITO', 'OLMOS SP', 'MARCIO', 'FELIPE LAGUNA', 'CREMOSO SORVETES'],
            'Producto': ['CUPUAÇU 8,5 (160KG)', 'AÇAI MÉDIO 8,70', 'AÇAI MÉDIO 8,70', 'AÇAI MÉDIO 8,70', 'AÇAI MÉDIO 8,70'],
            'Kg': [160.0, 3360.0, 1120.0, 2240.0, 3360.0],
            'Valor_BRL': [1360.0, 29231.99, 9744.0, 19488.0, 29231.99], # Siempre en Reales
            'Comissao_BRL': [27.2, 584.64, 194.88, 389.76, 584.64]
        }
        st.session_state['df_data'] = pd.DataFrame(data)

    # 2. Historial (Logs)
    if 'df_log' not in st.session_state:
        st.session_state['df_log'] = pd.DataFrame(columns=['Timestamp', 'Action', 'Details'])

# --- FUNCIÓN: REGISTRAR EN HISTORIAL ---
def add_log(action, details):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{'Timestamp': now, 'Action': action, 'Details': details}])
    st.session_state['df_log'] = pd.concat([new_log, st.session_state['df_log']], ignore_index=True)

# --- FUNCIÓN: CONVERTIR MONEDA VISUAL ---
def get_converted_df(df, lang):
    rate = RATES[lang]["rate"]
    symbol = RATES[lang]["symbol"]
    
    df_view = df.copy()
    df_view['Valor_View'] = df_view['Valor_BRL'] * rate
    df_view['Comissao_View'] = df_view['Comissao_BRL'] * rate
    return df_view, symbol

# --- APLICACIÓN PRINCIPAL ---
def main():
    init_session()
    
    # --- BARRA LATERAL ---
    st.sidebar.header("🍇 Xingu Admin")
    lang = st.sidebar.selectbox("Idioma / Language", ["Português", "Español", "English"])
    t = translations[lang]
    
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"🛠 {t['nav_manage']}")
    mode = st.sidebar.radio("Modo", [t['mode_view'], t['mode_add'], t['mode_edit'], t['mode_del']])

    # --- LÓGICA DE GESTIÓN (CRUD) ---
    
    # 1. MODO AGREGAR
    if mode == t['mode_add']:
        st.sidebar.markdown("---")
        with st.sidebar.form("add_form"):
            f_emp = st.text_input(t['col_company'])
            f_prod = st.selectbox(t['col_product'], ["AÇAI MÉDIO 8,70", "AÇAI POP 6,6", "CUPUAÇU 8,5 (160KG)", "Outro"])
            f_kg = st.number_input("Kg", min_value=0.0)
            f_val = st.number_input("Valor (R$ - Reais)", min_value=0.0)
            
            if st.form_submit_button(t['btn_add']):
                new_row = {
                    'Empresa': f_emp, 'Producto': f_prod, 'Kg': f_kg,
                    'Valor_BRL': f_val, 'Comissao_BRL': f_val * 0.02
                }
                st.session_state['df_data'] = pd.concat([st.session_state['df_data'], pd.DataFrame([new_row])], ignore_index=True)
                add_log("CREATE", f"Add: {f_emp} - {f_prod} (R$ {f_val})")
                st.sidebar.success(t['msg_success'])

    # 2. MODO EDITAR
    elif mode == t['mode_edit']:
        st.sidebar.markdown("---")
        df = st.session_state['df_data']
        # Selector para elegir qué fila editar (Muestra Empresa y Producto)
        select_options = df.index.astype(str) + " - " + df['Empresa'] + " (" + df['Producto'] + ")"
        selected_idx = st.sidebar.selectbox("Seleccione ID", df.index, format_func=lambda x: f"{x} - {df.iloc[x]['Empresa']}")
        
        # Formulario con los valores actuales precargados
        if selected_idx is not None:
            current_row = df.loc[selected_idx]
            with st.sidebar.form("edit_form"):
                e_emp = st.text_input(t['col_company'], value=current_row['Empresa'])
                e_prod = st.text_input(t['col_product'], value=current_row['Producto'])
                e_kg = st.number_input("Kg", value=float(current_row['Kg']))
                e_val = st.number_input("Valor (R$)", value=float(current_row['Valor_BRL']))
                
                if st.form_submit_button(t['btn_save']):
                    st.session_state['df_data'].at[selected_idx, 'Empresa'] = e_emp
                    st.session_state['df_data'].at[selected_idx, 'Producto'] = e_prod
                    st.session_state['df_data'].at[selected_idx, 'Kg'] = e_kg
                    st.session_state['df_data'].at[selected_idx, 'Valor_BRL'] = e_val
                    st.session_state['df_data'].at[selected_idx, 'Comissao_BRL'] = e_val * 0.02
                    
                    add_log("UPDATE", f"Edit ID {selected_idx}: {e_emp} (R$ {e_val})")
                    st.sidebar.success(t['msg_success'])
                    st.experimental_rerun()

    # 3. MODO ELIMINAR
    elif mode == t['mode_del']:
        st.sidebar.markdown("---")
        df = st.session_state['df_data']
        to_del = st.sidebar.multiselect("Seleccionar para borrar", df.index, format_func=lambda x: f"{x}: {df.iloc[x]['Empresa']}")
        
        if st.sidebar.button(t['btn_del']):
            if to_del:
                # Guardamos nombres para el log antes de borrar
                names = ", ".join(df.loc[to_del, 'Empresa'].tolist())
                st.session_state['df_data'] = df.drop(to_del).reset_index(drop=True)
                add_log("DELETE", f"Removed: {names}")
                st.sidebar.success(t['msg_success'])
                st.experimental_rerun()

    # --- PANTALLA PRINCIPAL ---
    
    # Preparar datos para visualizar (Moneda convertida)
    df_main = st.session_state['df_data']
    df_view, symbol = get_converted_df(df_main, lang)
    
    # Renombrar columnas para la tabla
    df_table = df_view.rename(columns={
        'Empresa': t['col_company'],
        'Producto': t['col_product'],
        'Kg': t['col_qty'],
        'Valor_View': f"{t['col_value']} ({symbol})",
        'Comissao_View': f"{t['col_comm']} ({symbol})"
    })
    
    # Seleccionar solo columnas visibles
    cols_final = [t['col_company'], t['col_product'], t['col_qty'], f"{t['col_value']} ({symbol})", f"{t['col_comm']} ({symbol})"]
    df_table = df_table[cols_final]

    st.title(f"{t['menu']}")
    
    # KPIS
    k1, k2, k3 = st.columns(3)
    k1.metric(f"{t['col_value']}", f"{symbol} {df_view['Valor_View'].sum():,.2f}")
    k2.metric(f"{t['col_qty']}", f"{df_view['Kg'].sum():,.0f} Kg")
    k3.metric(f"{t['col_comm']}", f"{symbol} {df_view['Comissao_View'].sum():,.2f}")

    st.divider()

    # PESTAÑAS (DATOS vs HISTORIAL)
    tab1, tab2 = st.tabs(["📊 " + t['mode_view'], "🕒 " + t['log_title']])

    with tab1:
        c_chart, c_table = st.columns([1, 2])
        with c_chart:
            st.subheader("Mix de Productos")
            fig = px.pie(df_view, values='Valor_View', names='Producto', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c_table:
            st.subheader("Detalle")
            st.dataframe(df_table, use_container_width=True, height=400)

    with tab2:
        st.subheader(f"{t['log_title']}")
        st.dataframe(
            st.session_state['df_log'], 
            use_container_width=True,
            column_config={
                "Timestamp": st.column_config.TextColumn(t['log_time']),
                "Action": st.column_config.TextColumn(t['log_action']),
                "Details": st.column_config.TextColumn(t['log_desc']),
            }
        )

if __name__ == "__main__":
    main()