import subprocess
import sys
import os
from flask import Flask, Response, abort, request 

# Define tu excepción personalizada
class ReportGenerationError(Exception):
    pass

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JASPER_DIR = os.path.join(BASE_DIR, "jasper")


JAR_PATH = os.path.join(JASPER_DIR, "luciajasper.jar")
LIB_PATH = os.path.join(JASPER_DIR, "lib", "*")  # Java maneja el * en -cp
MAIN_CLASS = "luciareportes.GenerarReporte"

JAVA_WORKING_DIR = JASPER_DIR

def generate_and_get_pdf_path(cedula):
    """
    Ejecuta Java, que guarda el PDF en disco y devuelve la ruta del archivo.
    """
    classpath = f"{JAR_PATH}:{LIB_PATH}"
    # Solo pasamos la cédula como argumento a Java
    comando = ["java", "-cp", classpath, MAIN_CLASS, str(cedula)]
    generated_pdf_path = None # Para guardar la ruta que Java devuelve

    try:
        print(f"Ejecutando en '{JAVA_WORKING_DIR}': {' '.join(comando)}", file=sys.stderr)
        result = subprocess.run(
            comando,
            capture_output=True, # Captura stdout (ruta del archivo) y stderr (errores Java)
            check=True,          # Lanza error si Java sale con código != 0
            timeout=45,          # Aumenta timeout si los reportes son grandes
            text=True,           # Decodifica stdout/stderr como texto
            encoding='utf-8',    # Especifica encoding
            cwd=JAVA_WORKING_DIR # Ejecuta Java en este directorio de trabajo
                                 # ¡Muy importante si Java usa System.getProperty("user.dir")!
        )

        # Java debería imprimir la ruta absoluta del archivo a stdout
        generated_pdf_path = result.stdout.strip()

        # --- Verificaciones ---
        if not generated_pdf_path:
             stderr_info = result.stderr.strip() if result.stderr else "No stderr output."
             raise ReportGenerationError(f"Java terminó exitosamente pero no devolvió la ruta del archivo. Stderr: {stderr_info}")

        # Verifica que la ruta devuelta sea absoluta (más seguro)
        if not os.path.isabs(generated_pdf_path):
             raise ReportGenerationError(f"Java devolvió una ruta relativa o inválida: {generated_pdf_path}")

        # Verifica si el archivo realmente existe en esa ruta
        if not os.path.exists(generated_pdf_path):
             stderr_info = result.stderr.strip() if result.stderr else "No stderr output."
             raise ReportGenerationError(f"Java indicó el archivo {generated_pdf_path}, pero no se encontró. Stderr: {stderr_info}")

        # Verifica si el archivo tiene contenido (opcional pero recomendado)
        if os.path.getsize(generated_pdf_path) == 0:
            print(f"Advertencia: El archivo PDF generado {generated_pdf_path} está vacío.", file=sys.stderr)
            # Puedes decidir lanzar un error aquí o permitir servir archivos vacíos

        print(f"Java generó el archivo: {generated_pdf_path}", file=sys.stderr)
        return generated_pdf_path # Devuelve la ruta del archivo creado

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() if e.stderr else "No stderr output."
        print(f"Error en Java (Código {e.returncode}) al generar reporte para {cedula}. Stderr:\n{error_output}", file=sys.stderr)
        # No necesitamos borrar archivo aquí, Java debería manejarlo o no se creó
        raise ReportGenerationError(f"Java process failed: {error_output}") from e
    except FileNotFoundError:
        print(f"Error: Comando 'java' o archivo JAR no encontrado en la configuración de Python.", file=sys.stderr)
        raise FileNotFoundError(f"Command 'java' or JAR/Class not found in Python config.")
    except subprocess.TimeoutExpired:
        print(f"Error: Timeout al generar reporte para {cedula}.", file=sys.stderr)
        raise ReportGenerationError(f"Report generation timed out for cedula {cedula}.")
    except Exception as e:
         print(f"Error inesperado en Python durante la llamada a Java: {e}", file=sys.stderr)
         raise # Relanza la excepción para manejo en la ruta Flask






@app.route('/api/reporte/<int:cedula>', methods=['GET'])
def servir_reporte_api(cedula):
    """Ruta API para generar y servir el reporte PDF."""
    pdf_path = None # Guardar la ruta para poder borrarla en finally
    try:
        # 1. Llamar a la función que ejecuta Java y obtiene la ruta del PDF
        pdf_path = generate_and_get_pdf_path(cedula)

        # 2. Leer los datos binarios del archivo PDF generado
        print(f"Leyendo archivo: {pdf_path}", file=sys.stderr)
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        print(f"Leídos {len(pdf_data)} bytes.", file=sys.stderr)

        # (Opcional) Manejo de archivo vacío si no se hizo antes
        if not pdf_data:
             print(f"Error: Intentando servir archivo PDF vacío desde {pdf_path}", file=sys.stderr)
             abort(500, description="El reporte generado está vacío.")

        # 3. Crear la respuesta Flask
        response = Response(pdf_data, mimetype='application/pdf')
        # Sugiere al navegador mostrarlo en línea en lugar de descargar
        response.headers['Content-Disposition'] = f'inline; filename="estracto_sueldo_{cedula}.pdf"'
        print(f"Enviando respuesta PDF para cédula {cedula}", file=sys.stderr)
        return response

    except ReportGenerationError as e:
        # Error específico durante la generación en Java
        print(f"Error (ReportGenerationError) en API para cédula {cedula}: {e}", file=sys.stderr)
        abort(500, description=f"Error al generar el reporte PDF: {e}")
    except FileNotFoundError as e:
         # Error si Java, JAR, o el PDF generado no se encuentran donde se espera
         print(f"Error (FileNotFoundError) en API para cédula {cedula}: {e}", file=sys.stderr)
         abort(500, description=f"Error de configuración o archivo no encontrado: {e}")
    except IOError as e:
         # Error al leer el archivo PDF generado
         print(f"Error (IOError) leyendo el PDF en API para cédula {cedula}: {e}", file=sys.stderr)
         if pdf_path:
             print(f"El archivo problemático era: {pdf_path}", file=sys.stderr)
         abort(500, description=f"Error al leer el archivo del reporte generado: {e}")
    except Exception as e:
        # Cualquier otro error inesperado
        print(f"Error (inesperado) en API para cédula {cedula}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr) # Imprime el stack trace completo
        abort(500, description="Ocurrió un error interno inesperado.")

    finally:
        # --- 4. Limpieza: Borrar el archivo PDF temporal ---
        # Esto se ejecuta SIEMPRE, incluso si hubo errores arriba (después de manejar el error)
        if pdf_path and os.path.exists(pdf_path):
            try:
                print(f"Intentando borrar archivo temporal: {pdf_path}", file=sys.stderr)
                os.remove(pdf_path)
                print(f"Archivo temporal {pdf_path} borrado.", file=sys.stderr)
            except OSError as e:
                # Es importante loggear esto, pero no necesariamente fallar la petición (que ya pudo haberse enviado o fallado)
                print(f"¡Error CRÍTICO al borrar archivo temporal {pdf_path}: {e}!", file=sys.stderr)
                # Considera un mecanismo de limpieza alternativo si esto pasa frecuentemente





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