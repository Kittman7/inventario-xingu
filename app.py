import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xingu Cloud Admin", page_icon="🍇", layout="wide")

# --- CONEXIÓN GOOGLE SHEETS ---
def get_google_services():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["google_credentials"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Abre el archivo
    book = client.open("Inventario_Xingu_DB")
    return book

# --- FUNCIONES DE BASE DE DATOS ---
def registrar_historial(book, accion, detalles):
    try:
        sheet_log = book.worksheet("Historial")
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_log.append_row([hora, accion, detalles])
    except:
        st.warning("No se encontró la hoja 'Historial'. Crea una pestaña nueva con ese nombre en tu Google Sheet.")

# --- INTERFAZ PRINCIPAL ---
def main():
    st.title("🍇 Xingu Fruit - Sistema Completo")
    
    # Intentar conexión
    try:
        book = get_google_services()
        sheet = book.sheet1 # La hoja de datos
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()

    # MENU DE NAVEGACIÓN
    menu = st.sidebar.radio("Menú", ["📝 Registrar Venta", "🛠️ Administrar (Editar/Borrar)", "📜 Ver Historial"])

    # ---------------- SECCIÓN 1: REGISTRAR ----------------
    if menu == "📝 Registrar Venta":
        st.header("Nueva Venta")
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            emp = c1.text_input("Empresa")
            prod = c2.selectbox("Producto", ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"])
            kg = c1.number_input("Kg", min_value=0.0, step=10.0)
            val_brl = c2.number_input("Valor (R$)", min_value=0.0, step=100.0)
            
            if st.form_submit_button("💾 Guardar Venta"):
                if emp:
                    row = [emp, prod, kg, val_brl, val_brl * 0.02, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    sheet.append_row(row)
                    
                    # Guardar en historial
                    registrar_historial(book, "CREAR", f"Venta agregada: {emp} ({kg}kg)")
                    st.success("¡Venta guardada exitosamente!")
                    st.balloons()
                else:
                    st.warning("El nombre de la empresa es obligatorio")

    # ---------------- SECCIÓN 2: ADMINISTRAR ----------------
    elif menu == "🛠️ Administrar (Editar/Borrar)":
        st.header("Modificar o Borrar Ventas")
        
        # Cargar datos actuales
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Crear una lista para seleccionar (usamos el índice + nombre)
            opciones = [f"{i+2}. {row['Empresa']} - {row['Producto']} ({row['Fecha_Registro']})" for i, row in df.iterrows()]
            seleccion = st.selectbox("🔍 Selecciona la venta a modificar:", options=opciones)
            
            # Obtener el número de fila real en Google Sheets (Índice + 2 porque hay encabezado)
            index_selec = opciones.index(seleccion)
            fila_real = index_selec + 2 
            datos_actuales = df.iloc[index_selec]

            st.info(f"Editando fila: {fila_real}")
            
            # Formulario de Edición
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                # Ponemos los valores actuales como valor por defecto (value=...)
                new_emp = c1.text_input("Empresa", value=datos_actuales['Empresa'])
                new_prod = c2.selectbox("Producto", ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"], index=["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"].index(datos_actuales['Producto']) if datos_actuales['Producto'] in ["AÇAI MÉDIO", "AÇAI POP", "CUPUAÇU", "Outro"] else 3)
                new_kg = c1.number_input("Kg", min_value=0.0, value=float(datos_actuales['Kg']))
                new_val = c2.number_input("Valor (R$)", min_value=0.0, value=float(datos_actuales['Valor_BRL']))
                
                col_save, col_del = st.columns([1,1])
                bot_update = col_save.form_submit_button("🔄 Actualizar Datos")
                bot_delete = col_del.form_submit_button("🗑️ BORRAR VENTA", type="primary")

                if bot_update:
                    # Actualizar celda por celda (gspread usa filas y columas: row, col)
                    # Empresa (Col 1), Prod (Col 2), Kg (Col 3), Val (Col 4), Comision (Col 5)
                    sheet.update_cell(fila_real, 1, new_emp)
                    sheet.update_cell(fila_real, 2, new_prod)
                    sheet.update_cell(fila_real, 3, new_kg)
                    sheet.update_cell(fila_real, 4, new_val)
                    sheet.update_cell(fila_real, 5, new_val * 0.02) # Recalcular comisión
                    
                    registrar_historial(book, "MODIFICAR", f"Fila {fila_real} actualizada: {new_emp}")
                    st.success("¡Datos actualizados!")
                    st.rerun()

                if bot_delete:
                    sheet.delete_rows(fila_real)
                    registrar_historial(book, "BORRAR", f"Venta de {datos_actuales['Empresa']} eliminada")
                    st.error("¡Venta eliminada!")
                    st.rerun()
            
            # Mostrar tabla completa abajo para referencia
            st.divider()
            st.dataframe(df)
            
        else:
            st.info("No hay datos para editar.")

    # ---------------- SECCIÓN 3: VER HISTORIAL ----------------
    elif menu == "📜 Ver Historial":
        st.header("Historial de Cambios")
        try:
            sheet_log = book.worksheet("Historial")
            logs = sheet_log.get_all_records()
            df_logs = pd.DataFrame(logs)
            if not df_logs.empty:
                # Ordenar para ver lo más reciente primero
                st.dataframe(df_logs.iloc[::-1])
            else:
                st.info("El historial está vacío.")
        except:
            st.error("No se encontró la hoja 'Historial'.")

if __name__ == "__main__":
    main()
