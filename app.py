import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xingu Cloud", page_icon="🍇", layout="wide")

# --- 1. DICCIONARIO DE IDIOMAS (EL CEREBRO DE LA TRADUCCIÓN) ---
# Aquí definimos cada palabra en los 3 idiomas
TR = {
    "Português": {
        "menu_dash": "📊 Painel (Gráficos)",
        "menu_add": "➕ Registrar Venda",
        "menu_admin": "🛠️ Administrar (Editar)",
        "menu_log": "📜 Histórico",
        "title_dash": "Visão Geral de Vendas",
        "total_val": "Valor Total",
        "total_kg": "Total Kg",
        "chart_title": "Vendas por Empresa",
        "form_emp": "Empresa",
        "form_prod": "Produto",
        "form_kg": "Quantidade (Kg)",
        "form_val": "Valor (R$)",
        "btn_save": "💾 Salvar Venda",
        "btn_update": "🔄 Atualizar Dados",
        "btn_delete": "🗑️ APAGAR VENDA",
        "msg_success": "Salvo com sucesso!",
        "msg_update": "Atualizado com sucesso!",
        "msg_delete": "Venda apagada!",
        "msg_confirm": "Tem certeza?",
        "select_edit": "🔍 Selecione para editar:",
        "log_action": "Ação",
        "log_details": "Detalhes"
    },
    "Español": {
        "menu_dash": "📊 Dashboard (Gráficos)",
        "menu_add": "➕ Registrar Venta",
        "menu_admin": "🛠️ Administrar (Editar)",
        "menu_log": "📜 Historial",
        "title_dash": "Resumen de Ventas",
        "total_val": "Valor Total",
        "total_kg": "Total Kg",
        "chart_title": "Ventas por Empresa",
        "form_emp": "Empresa",
        "form_prod": "Producto",
        "form_kg": "Cantidad (Kg)",
        "form_val": "Valor (R$)",
        "btn_save": "💾 Guardar Venta",
        "btn_update": "🔄 Actualizar Datos",
        "btn_delete": "🗑️ BORRAR VENTA",
        "msg_success": "¡Guardado con éxito!",
        "msg_update": "¡Actualizado con éxito!",
        "msg_delete": "¡Venta eliminada!",
        "msg_confirm": "Seguro?",
        "select_edit": "🔍 Selecciona para editar:",
        "log_action": "Acción",
        "log_details": "Detalles"
    },
    "English": {
        "menu_dash": "📊 Dashboard (Charts)",
        "menu_add": "➕ Register Sale",
        "menu_admin": "🛠️ Manage (Edit)",
        "menu_log": "📜 History Log",
        "title_dash": "Sales Overview",
        "total_val": "Total Value",
        "total_kg": "Total Kg",
        "chart_title": "Sales by Company",
        "form_emp": "Company",
        "form_prod": "Product",
        "form_kg": "Quantity (Kg)",
        "form_val": "Value (R$)",
        "btn_save": "💾 Save Sale",
        "btn_update": "🔄 Update Data",
        "btn_delete": "🗑️ DELETE SALE",
        "msg_success": "Saved successfully!",
        "msg_update": "Updated successfully!",
        "msg_delete": "Sale deleted!",
        "msg_confirm": "Are you sure?",
        "select_edit": "🔍 Select to edit:",
        "log_action": "Action",
        "log_details": "Details"
    }
}

# Tasas de cambio
RATES = {
    "Português": {"symbol": "R$", "rate": 1.0},
    "Español":   {"symbol": "CLP $", "rate": 165.0},
    "English":   {"symbol": "USD $", "rate": 0.18}
}

# --- 2. CONEXIÓN A GOOGLE ---
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
        pass # Si falla el historial, no rompemos la app

# --- 3. APP PRINCIPAL ---
def main():
    # --- BARRA LATERAL (IDIOMA) ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50) # Icono decorativo
    lang = st.sidebar.selectbox("Language / Idioma", ["Español", "Português", "English"])
    
    # Cargar diccionario del idioma seleccionado
    t = TR[lang]
    rate = RATES[lang]["rate"]
    symbol = RATES[lang]["symbol"]

    st.title(f"🍇 Xingu Fruit - {lang}")

    # Conexión
    try:
        book = get_google_services()
        sheet = book.sheet1
    except Exception as e:
        st.error(f"Error Conexión: {e}")
        st.stop()

    # --- MENÚ PRINCIPAL (TRADUCIDO) ---
    opciones_menu = [t['menu_dash'], t['menu_add'], t['menu_admin'], t['menu_log']]
    menu = st.sidebar.radio("Navegación", opciones_menu)

    # ==========================================
    # 📊 SECCIÓN 1: DASHBOARD (GRÁFICOS)
    # ==========================================
    if menu == t['menu_dash']:
        st.header(t['title_dash'])
        
        # Leer datos
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
        except:
            df = pd.DataFrame()

        if not df.empty:
            # Convertir a números
            df['Valor_BRL'] = pd.to_numeric(df['Valor_BRL'], errors='coerce').fillna(0)
            df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce').fillna(0)
            
            # Crear columna con moneda convertida
            df['Valor_View'] = df['Valor_BRL'] * rate

            # TARJETAS DE TOTALES (KPIs)
            c1, c2, c3 = st.columns(3)
            total_dinero = df['Valor_View'].sum()
            total_kg = df['Kg'].sum()
            
            c1.metric(f"{t['total_val']} ({symbol})", f"{symbol} {total_dinero:,.2f}")
            c2.metric(t['total_kg'], f"{total_kg:,.0f} Kg")
            c3.metric("Total Ventas", len(df))

            st.divider()

            # GRÁFICO DE BARRAS
            # Usamos Plotly y le ponemos el título traducido
            fig = px.bar(
                df, 
                x='Empresa', 
                y='Valor_View', 
                color='Producto',
                title=f"{t['chart_title']} ({symbol})",
                text_auto='.2s',
                labels={'Valor_View': f"Valor ({symbol})", 'Empresa': t['form_emp']}
            )
            fig.update_layout(xaxis_title=t['form_emp'], yaxis_title=f"Valor ({symbol})")
            st.plotly_chart(fig, use_container_width=True)

            # Tabla abajo
            with st.expander("Ver Tabla de Datos"):
                st.dataframe(df)
        else:
            st.info("Ainda não há dados / No hay datos todavía.")

    # ==========================================
    # ➕ SECCIÓN 2: REGISTRAR
    # ==========================================
    elif menu == t['menu_add']:
        st.header(t['menu_add'])
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            emp = c1.text_input(t['form_emp'])
            prod = c2.selectbox(t['form_prod'], ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"])
            kg = c1.number_input(t['form_kg'], min_value=0.0, step=10.0)
            val_brl = c2.number_input(t['form_val'], min_value=0.0, step=100.0)
            
            if st.form_submit_button(t['btn_save']):
                if emp:
                    row = [emp, prod, kg, val_brl, val_brl * 0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    registrar_historial(book, "NEW", f"{emp} - {kg}kg")
                    st.success(t['msg_success'])
                    st.balloons()
                else:
                    st.warning("Nombre obligatorio / Nome obrigatório")

    # ==========================================
    # 🛠️ SECCIÓN 3: ADMINISTRAR (EDITAR/BORRAR)
    # ==========================================
    elif menu == t['menu_admin']:
        st.header(t['menu_admin'])
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Lista para seleccionar
            opciones = [f"{i+2}. {row['Empresa']} | {row['Producto']} | R$ {row['Valor_BRL']}" for i, row in df.iterrows()]
            seleccion = st.selectbox(t['select_edit'], options=opciones)
            
            index_selec = opciones.index(seleccion)
            fila_real = index_selec + 2 
            datos = df.iloc[index_selec]

            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                # Valores por defecto vienen de la base de datos
                new_emp = c1.text_input(t['form_emp'], value=datos['Empresa'])
                # Lógica para el selectbox (si el producto no está en la lista, usa "Outro")
                lista_prods = ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"]
                idx_prod = lista_prods.index(datos['Producto']) if datos['Producto'] in lista_prods else 3
                
                new_prod = c2.selectbox(t['form_prod'], lista_prods, index=idx_prod)
                new_kg = c1.number_input(t['form_kg'], min_value=0.0, value=float(datos['Kg']))
                new_val = c2.number_input(t['form_val'], min_value=0.0, value=float(datos['Valor_BRL']))
                
                c_save, c_del = st.columns([1,1])
                if c_save.form_submit_button(t['btn_update']):
                    sheet.update_cell(fila_real, 1, new_emp)
                    sheet.update_cell(fila_real, 2, new_prod)
                    sheet.update_cell(fila_real, 3, new_kg)
                    sheet.update_cell(fila_real, 4, new_val)
                    sheet.update_cell(fila_real, 5, new_val * 0.02)
                    registrar_historial(book, "UPDATE", f"Fila {fila_real}: {new_emp}")
                    st.success(t['msg_update'])
                    st.rerun()

                if c_del.form_submit_button(t['btn_delete'], type="primary"):
                    sheet.delete_rows(fila_real)
                    registrar_historial(book, "DELETE", f"{datos['Empresa']}")
                    st.error(t['msg_delete'])
                    st.rerun()
        else:
            st.info("Sin datos / Sem dados")

    # ==========================================
    # 📜 SECCIÓN 4: HISTORIAL
    # ==========================================
    elif menu == t['menu_log']:
        st.header(t['menu_log'])
        try:
            sheet_log = book.worksheet("Historial")
            logs = sheet_log.get_all_records()
            df_logs = pd.DataFrame(logs)
            if not df_logs.empty:
                st.dataframe(df_logs.iloc[::-1], use_container_width=True)
            else:
                st.info("Log vacío")
        except:
            st.warning("Crea la hoja 'Historial' en Google Sheets.")

if __name__ == "__main__":
    main()
