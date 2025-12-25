import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import io
import xlsxwriter
import urllib.parse

# ==========================================
# 🔐 CONFIGURACIÓN DE ACCESO
# ==========================================
NOMBRE_EMPRESA = "Xingu CEO"
ICONO_APP = "🍇"
SENHA_ADMIN = "julio777"  # <--- CORREGIDO: Todo en minúsculas
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=ICONO_APP, layout="wide")

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
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- VERIFICAR CONEXIÓN (DIAGNÓSTICO) ---
def get_data():
    # 1. Verificar si existen las llaves
    if "google_credentials" not in st.secrets:
        st.error("🚨 ERROR CRÍTICO: Faltan las llaves de Google.")
        st.info("Ve a 'Settings' -> 'Secrets' en Streamlit y pega las credenciales de nuevo.")
        st.stop()
    
    # 2. Intentar conectar
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
        client = gspread.authorize(creds)
        book = client.open("Inventario_Xingu_DB")
        return book
    except Exception as e:
        st.error(f"🚨 Error conectando con la Hoja de Cálculo: {e}")
        st.stop()

# --- LOGIN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown(f"<h1 style='text-align: center;'>🔒 {NOMBRE_EMPRESA}</h1>", unsafe_allow_html=True)
        
        # Estado de la conexión
        st.success("✅ Sistema Online")
        
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            # Convertimos lo que escribe el usuario a minúsculas y quitamos espacios
            # Así si escribe "Julio777 " o "JULIO777", funcionará igual.
            pass_limpia = password.strip().lower()
            
            if pass_limpia == SENHA_ADMIN:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error(f"🚫 Incorrecto. (Se esperaba: '{SENHA_ADMIN}')")
    return False

# --- MAPA DE MESES ---
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

MONTHS_UI = {
    "Português": MESES_PT,
    "Español": {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"},
    "English": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
}

# --- IDIOMAS ---
TR = {
    "Português": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Admin", "📜 Log"],
        "metrics": ["Faturamento", "Volume (Kg)", "Comissão", "Ticket Médio", "Melhor Cliente"],
        "headers": ["Visão Geral", "Nova Venda"],
        "cols": {"emp": "Empresa", "prod": "Produto", "kg": "Kg", "val": "Valor (R$)", "com": "Comissão"},
        "btn": "Confirmar Venda",
        "excel": "Baixar Excel"
    },
    "Español": {
        "tabs": ["📊 Dashboard", "➕ Vender", "🛠️ Admin", "📜 Log"],
        "metrics": ["Facturación", "Volumen (Kg)", "Comisión", "Ticket Medio", "Mejor Cliente"],
        "headers": ["Visión General", "Nueva Venta"],
        "cols": {"emp": "Empresa", "prod": "Producto", "kg": "Kg", "val": "Valor ($)", "com": "Comisión"},
        "btn": "Confirmar Venta",
        "excel": "Descargar Excel"
    },
    "English": {
        "tabs": ["📊 Dashboard", "➕ Sell", "🛠️ Admin", "📜 Log"],
        "metrics": ["Revenue", "Volume (Kg)", "Commission", "Avg Ticket", "Top Client"],
        "headers": ["Overview", "New Sale"],
        "cols": {"emp": "Company", "prod": "Product", "kg": "Kg", "val": "Value ($)", "com": "Commission"},
        "btn": "Confirm Sale",
        "excel": "Download Excel"
    }
}

def log_action(book, action, detail):
    try:
        book.worksheet("Historial").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, detail])
    except: pass

# --- APP PRINCIPAL ---
def main():
    if not check_password():
        return

    # Si pasa el login, cargamos la App
    book = get_data() # Conectamos con Google
    
    with st.sidebar:
        st.title(f"{ICONO_APP} Menú")
        lang = st.selectbox("Idioma", ["Português", "Español", "English"])
        
        if st.button("Cerrar Sesión"):
            st.session_state.password_correct = False
            st.rerun()
    
    t = TR[lang]
    sheet = book.sheet1
    df = pd.DataFrame(sheet.get_all_records())

    # Limpieza de datos (Evita errores de tabla)
    if not df.empty:
        for c in ['Valor_BRL', 'Kg', 'Comissao_BRL']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        empresas = sorted(list(set(df['Empresa'].astype(str))))
        productos = sorted(list(set(["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU"] + list(df['Producto'].astype(str)))))
    else:
        empresas, productos = [], ["AÇAI POP"]

    # PESTAÑAS
    tab1, tab2, tab3, tab4 = st.tabs(t['tabs'])

    # 1. DASHBOARD
    with tab1:
        st.header(t['headers'][0])
        if not df.empty:
            total = df['Valor_BRL'].sum()
            kg = df['Kg'].sum()
            com = df['Comissao_BRL'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric(t['metrics'][0], f"R$ {total:,.2f}")
            c2.metric(t['metrics'][1], f"{kg:,.0f} kg")
            c3.metric(t['metrics'][2], f"R$ {com:,.2f}")
            
            st.divider()
            
            # TABLA SIMPLE (Estable)
            df_show = df.copy()
            # Formato fecha simple
            df_show['Fecha'] = pd.to_datetime(df_show['Fecha_Registro'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                df_show[['Fecha', 'Empresa', 'Producto', 'Kg', 'Valor_BRL', 'Comissao_BRL']].iloc[::-1],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valor_BRL": st.column_config.NumberColumn(t['cols']['val'], format="R$ %.2f"),
                    "Comissao_BRL": st.column_config.NumberColumn(t['cols']['com'], format="R$ %.2f"),
                    "Kg": st.column_config.NumberColumn(t['cols']['kg'], format="%.1f kg")
                }
            )
            
            # Excel Download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_show.to_excel(writer, index=False)
            st.download_button(t['excel'], data=buffer, file_name="Reporte_Xingu.xlsx", mime="application/vnd.ms-excel", type="primary")

    # 2. VENDER
    with tab2:
        st.header(t['headers'][1])
        c1, c2 = st.columns(2)
        
        # Selectores inteligentes
        emp = c1.selectbox(t['cols']['emp'], ["✨ Nueva..."] + empresas)
        if emp == "✨ Nueva...": emp = c1.text_input("Escribe Nombre Empresa")
        
        prod = c2.selectbox(t['cols']['prod'], ["✨ Nuevo..."] + productos)
        if prod == "✨ Nuevo...": prod = c2.text_input("Escribe Nombre Producto")
        
        kg = c1.number_input(t['cols']['kg'], step=1.0)
        val = c2.number_input(t['cols']['val'], step=100.0)
        
        if st.button(t['btn'], type="primary"):
            if emp and prod:
                ahora = datetime.now()
                mes = MESES_PT[ahora.month]
                # Guardar en DB
                sheet.append_row([emp, prod, kg, val, val*0.02, ahora.strftime("%Y-%m-%d %H:%M:%S"), mes])
                log_action(book, "NEW", f"{emp} | {val}")
                st.success("✅ Guardado Exitosamente")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("⚠️ Faltan datos (Empresa o Producto)")

    # 3. ADMIN
    with tab3:
        st.write("🔧 Gestión rápida")
        if not df.empty:
            for i, r in df.tail(5).iloc[::-1].iterrows():
                # Mostrar últimas 5 para borrar si hay error
                with st.expander(f"🗑️ Borrar: {r['Empresa']} ({r['Kg']}kg)"):
                    if st.button("Confirmar Borrado", key=f"d{i}"):
                        rows = sheet.get_all_values()
                        for idx, row in enumerate(rows):
                            # Buscamos por la fecha exacta para no equivocarnos
                            if str(r['Fecha_Registro']) in row:
                                sheet.delete_rows(idx + 1)
                                log_action(book, "BORRAR", f"{r['Empresa']}")
                                st.success("Eliminado")
                                time.sleep(1)
                                st.rerun()

    # 4. LOG
    with tab4:
        try:
            logs = pd.DataFrame(book.worksheet("Historial").get_all_records())
            if not logs.empty:
                st.dataframe(logs.iloc[::-1], use_container_width=True)
        except: st.info("No hay historial todavía.")

if __name__ == "__main__":
    main()
