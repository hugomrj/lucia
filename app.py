import subprocess
import sys
import os
from flask import Flask, Response, abort, request
from generar_pdf import JAVA_WORKING_DIR, ReportGenerationError, generate_and_get_pdf_path



app = Flask(__name__)




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




