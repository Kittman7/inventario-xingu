import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xingu Cloud", page_icon="🍇", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Error de conexión. Revisa los 'Secrets' en Streamlit Cloud.")
    st.stop()

# --- MONEDAS ---
RATES = {
    "Português": {"symbol": "R$", "rate": 1.0},
    "Español":   {"symbol": "CLP $", "rate": 165.0},
    "English":   {"symbol": "USD $", "rate": 0.18}
}

translations = {
    "Português": {"menu": "Sistema Cloud", "add": "Adicionar Venda", "col_emp": "Empresa", "col_prod": "Produto", "col_kg": "Kg", "col_val": "Valor (R$)", "success": "Salvo no Google Sheets!"},
    "Español": {"menu": "Sistema Cloud", "add": "Agregar Venta", "col_emp": "Empresa", "col_prod": "Producto", "col_kg": "Kg", "col_val": "Valor (R$)", "success": "¡Guardado en Google Sheets!"},
    "English": {"menu": "Cloud System", "add": "Add Sale", "col_emp": "Company", "col_prod": "Product", "col_kg": "Kg", "col_val": "Value (R$)", "success": "Saved to Google Sheets!"}
}

# --- FUNCIÓN LEER DATOS ---
def get_data():
    try:
        # ttl=0 obliga a leer siempre datos frescos de la nube
        df = conn.read(worksheet="Hoja 1", ttl=0)
        return df
    except Exception:
        return pd.DataFrame()

# --- APP PRINCIPAL ---
def main():
    st.title("🍇 Xingu Fruit - Base de Datos Real")
    
    # Selector Idioma
    lang = st.sidebar.selectbox("Idioma", ["Português", "Español", "English"])
    t = translations[lang]
    rate = RATES[lang]["rate"]
    symbol = RATES[lang]["symbol"]

    # 1. FORMULARIO DE INGRESO
    st.sidebar.header(f"➕ {t['add']}")
    with st.sidebar.form("entry_form"):
        emp = st.text_input(t['col_emp'])
        prod = st.selectbox(t['col_prod'], ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"])
        kg = st.number_input(t['col_kg'], min_value=0.0, step=10.0)
        val_brl = st.number_input(t['col_val'], min_value=0.0, step=100.0)
        
        submitted = st.form_submit_button("💾 Guardar / Salvar")
        
        if submitted and emp:
            # Preparar la nueva fila
            new_row = pd.DataFrame([{
                "Empresa": emp,
                "Producto": prod,
                "Kg": kg,
                "Valor_BRL": val_brl,
                "Comissao_BRL": val_brl * 0.02,
                "Fecha_Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            
            # Leer datos actuales, unir y subir todo
            try:
                current_df = get_data()
                if not current_df.empty:
                    updated_df = pd.concat([current_df, new_row], ignore_index=True)
                else:
                    updated_df = new_row
                
                conn.update(worksheet="Hoja 1", data=updated_df)
                st.success(t['success'])
                st.cache_data.clear() # Limpiar memoria
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # 2. MOSTRAR DATOS
    df = get_data()
    
    if not df.empty:
        # Limpieza de datos (asegurar que sean números)
        df['Valor_BRL'] = pd.to_numeric(df['Valor_BRL'], errors='coerce').fillna(0)
        df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce').fillna(0)
        
        # Convertir moneda
        df['Valor_View'] = df['Valor_BRL'] * rate
        
        # KPIs
        c1, c2 = st.columns(2)
        c1.metric(f"Total {symbol}", f"{df['Valor_View'].sum():,.2f}")
        c2.metric("Total Kg", f"{df['Kg'].sum():,.0f}")
        
        st.divider()
        
        # Tabla y Gráfico
        t1, t2 = st.tabs(["📋 Tabla", "📊 Gráfico"])
        
        with t1:
            st.dataframe(df)
            
        with t2:
            fig = px.bar(df, x='Empresa', y='Valor_View', color='Producto', title=f"Ventas en {symbol}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("La base de datos está vacía. ¡Agrega la primera venta en el menú lateral!")

if __name__ == "__main__":
    main()
