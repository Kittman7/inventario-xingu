import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xingu Cloud", page_icon="🍇", layout="wide")

# --- CONEXIÓN CLÁSICA A GOOGLE SHEETS ---
def get_google_sheet_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # AQUI ESTABA EL ERROR: Ahora usamos el nombre correcto [google_credentials]
    creds_dict = st.secrets["google_credentials"]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Abre la hoja
    sheet = client.open("Inventario_Xingu_DB").sheet1
    return sheet

# --- MONEDAS ---
RATES = {
    "Português": {"symbol": "R$", "rate": 1.0},
    "Español":   {"symbol": "CLP $", "rate": 165.0},
    "English":   {"symbol": "USD $", "rate": 0.18}
}

translations = {
    "Português": {"add": "Adicionar Venda", "col_emp": "Empresa", "col_prod": "Produto", "col_kg": "Kg", "col_val": "Valor (R$)", "success": "Salvo com sucesso!"},
    "Español": {"add": "Agregar Venta", "col_emp": "Empresa", "col_prod": "Producto", "col_kg": "Kg", "col_val": "Valor (R$)", "success": "¡Guardado con éxito!"},
    "English": {"add": "Add Sale", "col_emp": "Company", "col_prod": "Product", "col_kg": "Kg", "col_val": "Value (R$)", "success": "Saved successfully!"}
}

# --- APP PRINCIPAL ---
def main():
    st.title("🍇 Xingu Fruit - Versión Final")
    
    # Selector Idioma
    lang = st.sidebar.selectbox("Idioma", ["Português", "Español", "English"])
    t = translations[lang]
    rate = RATES[lang]["rate"]
    symbol = RATES[lang]["symbol"]

    # Intentar conexión
    try:
        sheet = get_google_sheet_data()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.info("Verifica que el nombre en Secrets sea [google_credentials] y que hayas compartido la hoja con el email del robot.")
        st.stop()

    # 1. FORMULARIO
    st.sidebar.header(f"➕ {t['add']}")
    with st.sidebar.form("entry_form"):
        emp = st.text_input(t['col_emp'])
        prod = st.selectbox(t['col_prod'], ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"])
        kg = st.number_input(t['col_kg'], min_value=0.0, step=10.0)
        val_brl = st.number_input(t['col_val'], min_value=0.0, step=100.0)
        
        if st.form_submit_button("💾 Guardar"):
            if emp:
                row = [
                    emp, 
                    prod, 
                    kg, 
                    val_brl, 
                    val_brl * 0.02, 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                sheet.append_row(row)
                st.success(t['success'])
                st.rerun()

    # 2. LEER Y MOSTRAR DATOS
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    except:
        df = pd.DataFrame()

    if not df.empty:
        df['Valor_BRL'] = pd.to_numeric(df['Valor_BRL'], errors='coerce').fillna(0)
        df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce').fillna(0)
        df['Valor_View'] = df['Valor_BRL'] * rate
        
        c1, c2 = st.columns(2)
        c1.metric(f"Total {symbol}", f"{df['Valor_View'].sum():,.2f}")
        c2.metric("Total Kg", f"{df['Kg'].sum():,.0f}")
        
        st.divider()
        
        t1, t2 = st.tabs(["Tabla", "Gráfico"])
        with t1:
            st.dataframe(df)
        with t2:
            fig = px.bar(df, x='Empresa', y='Valor_View', color='Producto')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Esperando datos... (Si acabas de crear la hoja, agrega una venta primero)")

if __name__ == "__main__":
    main()
