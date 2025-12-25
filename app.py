import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import io
import xlsxwriter

# ==========================================
# 🔧 ZONA DE DIAGNÓSTICO
# ==========================================
NOMBRE_EMPRESA = "Xingu CEO"
ICONO_APP = "🍇"
SENHA_ADMIN = "Julio777" 
# ==========================================

# --- CONFIGURACIÓN ---
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

# --- ESTILO ---
st.markdown("""
    <style>
    .stButton>button {width: 100%; font-weight: bold; height: 3em;}
    </style>
""", unsafe_allow_html=True)

# --- VERIFICADOR DE CONEXIÓN (EL CEREBRO) ---
def verificar_conexion():
    # 1. Verificar si existen los secretos
    if "google_credentials" not in st.secrets:
        st.error("🚨 ERROR CRÍTICO: Faltan los 'Secrets' de Google.")
        st.info("💡 Solución: Ve a Streamlit Cloud -> Settings -> Secrets y pega de nuevo las credenciales de Google (el texto largo con type: service_account).")
        st.stop()
    
    # 2. Intentar conectar
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
        client = gspread.authorize(creds)
        book = client.open("Inventario_Xingu_DB")
        return book
    except Exception as e:
        st.error(f"🚨 Error conectando con Google Sheets: {e}")
        st.warning("Verifica que el nombre de la hoja en Drive sea exactamente: Inventario_Xingu_DB")
        st.stop()

# --- SEGURIDAD ---
def login():
    if "acceso" not in st.session_state:
        st.session_state.acceso = False

    if st.session_state.acceso:
        return True

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title(f"🔒 Acceso {NOMBRE_EMPRESA}")
        
        # INDICADOR DE ESTADO
        st.success("✅ Base de Datos Conectada")
        
        pass_input = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", type="primary"):
            # Limpiamos espacios y comparamos
            if pass_input.strip() == SENHA_ADMIN:
                st.session_state.acceso = True
                st.rerun()
            else:
                st.error(f"⛔ Contraseña incorrecta. Escribiste: '{pass_input}'")
    return False

# --- APP PRINCIPAL ---
def main():
    # 1. Primero verificamos que Google funcione
    book = verificar_conexion()
    
    # 2. Luego pedimos contraseña
    if not login():
        return

    # SI LLEGA AQUÍ, TODO FUNCIONA
    with st.sidebar:
        st.header(f"{ICONO_APP} Menú")
        if st.button("Cerrar Sesión"):
            st.session_state.acceso = False
            st.rerun()
    
    # Lógica simplificada de pestañas
    t1, t2 = st.tabs(["📊 Dashboard", "➕ Vender"])
    
    sheet = book.sheet1
    try:
        df = pd.DataFrame(sheet.get_all_records())
    except:
        df = pd.DataFrame()

    with t1:
        st.title("Panel de Control")
        if not df.empty:
            # Corrección de tipos para evitar errores de suma
            # Convertimos todo a números forzosamente, los errores se vuelven 0
            df['Valor_BRL'] = pd.to_numeric(df['Valor_BRL'], errors='coerce').fillna(0)
            df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce').fillna(0)
            
            total = df['Valor_BRL'].sum()
            kilos = df['Kg'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Total Vendido", f"R$ {total:,.2f}")
            c2.metric("Total Kilos", f"{kilos:,.0f} kg")
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay ventas registradas aún.")

    with t2:
        st.header("Nueva Venta")
        c1, c2 = st.columns(2)
        cli = c1.text_input("Cliente")
        prod = c2.text_input("Producto")
        k = c1.number_input("Kilos", step=1.0)
        v = c2.number_input("Valor R$", step=10.0)
        
        if st.button("Guardar Venta", type="primary"):
            if cli and prod:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Guardamos como texto simple para evitar problemas
                sheet.append_row([cli, prod, k, v, v*0.02, ahora])
                st.success("¡Guardado!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Faltan datos")

if __name__ == "__main__":
    main()
