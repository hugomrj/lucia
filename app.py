import subprocess
import sys
import os
from flask import Flask, Response, abort, request, jsonify
import mysql.connector
from generar_pdf import JAVA_WORKING_DIR, ReportGenerationError, generate_and_get_pdf_path



app = Flask(__name__)



# Configuración de la base de datos
db_config = {
    "host": "127.0.0.1",
    "user": "lucia",
    "password": "admin123",
    "database": "lucia_database"
}




def obtener_trabajador_por_celular(celular):
    """Obtiene los datos del trabajador por número de celular."""
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True) #obtiene los datos en formato de diccionario
        consulta = """
            SELECT cedula, nombres, apellidos, celular
            FROM trabajador
            WHERE celular = %s
        """
        cursor.execute(consulta, (celular,))
        resultado = cursor.fetchone() #fetchone() obtiene un solo resultado
        return resultado
    except mysql.connector.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()







@app.route('/api/reporte/celular/<string:celular>', methods=['GET'])
def servir_reporte_por_celular(celular):
    """Ruta API para generar y servir el reporte PDF usando número de celular."""
    pdf_path = None 
    try:
        # Primero obtener la cédula asociada al celular
        trabajador = obtener_trabajador_por_celular(celular)
        
        if not trabajador:
            abort(404, description="No se encontró trabajador con ese número de celular")
        
        cedula = trabajador['cedula']
        
        # Llamar a la función que ejecuta Java y obtiene la ruta del PDF
        pdf_path = generate_and_get_pdf_path(cedula)

        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        if not pdf_data:
            abort(500, description="El reporte generado está vacío.")

        # Usar los datos del trabajador para el nombre del archivo
        filename = f"estracto_sueldo_{trabajador['nombres']}_{trabajador['apellidos']}.pdf"
        
        response = Response(pdf_data, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except ReportGenerationError as e:
        abort(500, description=f"Error al generar el reporte PDF: {e}")
    except Exception as e:
        abort(500, description=f"Error inesperado: {e}")

    finally:
        # Limpiar el archivo PDF temporal si existe
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass







@app.route('/api/reporte/<int:cedula>', methods=['GET'])
def servir_reporte_api(cedula):
    """Ruta API para generar y servir el reporte PDF."""
    pdf_path = None 
    try:
        # Llamar a la función que ejecuta Java y obtiene la ruta del PDF
        pdf_path = generate_and_get_pdf_path(cedula)

        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        if not pdf_data:
            abort(500, description="El reporte generado está vacío.")

        response = Response(pdf_data, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'inline; filename="estracto_sueldo_{cedula}.pdf"'
        return response

    except ReportGenerationError as e:
        abort(500, description=f"Error al generar el reporte PDF: {e}")
    except Exception as e:
        abort(500, description=f"Error inesperado: {e}")

    finally:
        # Limpiar el archivo PDF temporal si existe
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass






@app.route("/test")
def index():
    return "✅ aplicacion instalada correctamente", 200



# --- Punto de entrada ---
if __name__ == '__main__':
    # Verificar que el directorio de trabajo para Java exista (si se especificó)
    if JAVA_WORKING_DIR and not os.path.isdir(JAVA_WORKING_DIR):
         print(f"Error: El directorio de trabajo especificado para Java no existe: '{JAVA_WORKING_DIR}'", file=sys.stderr)
         sys.exit(1)
    elif JAVA_WORKING_DIR:
         print(f"Se ejecutará Java en el directorio: {JAVA_WORKING_DIR}")
    else:
         print(f"Se ejecutará Java en el directorio actual de Python: {os.getcwd()}")

    # Ejecutar la aplicación Flask
    # Asegúrate de que el puerto 5000 esté libre o cámbialo
    print("Iniciando servidor Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)




