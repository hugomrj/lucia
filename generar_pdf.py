import os
import subprocess

# Define tu excepción personalizada
class ReportGenerationError(Exception):
    pass


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JASPER_DIR = os.path.join(BASE_DIR, "jasper")

JAR_PATH = os.path.join(JASPER_DIR, "luciajasper.jar")
LIB_PATH = os.path.join(JASPER_DIR, "lib", "*")  # Java maneja el * en -cp
MAIN_CLASS = "luciareportes.GenerarReporte"

JAVA_WORKING_DIR = JASPER_DIR



def generate_and_get_pdf_path(cedula):
    # Función que ejecuta el comando Java para generar el reporte
    classpath = f"{JAR_PATH}:{LIB_PATH}"
    comando = ["java", "-cp", classpath, MAIN_CLASS, str(cedula)]
    generated_pdf_path = None  # Para guardar la ruta que Java devuelve

    try:
        result = subprocess.run(
            comando,
            capture_output=True, 
            check=True,          
            timeout=45,          
            text=True,           
            encoding='utf-8',    
            cwd=JAVA_WORKING_DIR 
        )

        generated_pdf_path = result.stdout.strip()

        if not generated_pdf_path or not os.path.isabs(generated_pdf_path) or not os.path.exists(generated_pdf_path):
            raise ReportGenerationError("Java no devolvió una ruta válida o el archivo no existe.")

        return generated_pdf_path  # Devuelve la ruta del archivo creado

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() if e.stderr else "No stderr output."
        raise ReportGenerationError(f"Java process failed: {error_output}") from e
    except Exception as e:
        raise ReportGenerationError(f"Error inesperado en Java: {e}") from e



