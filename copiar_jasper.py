import os
import shutil

# --- Configuración de rutas ---
RUTA_ORIGEN_LIB = "/home/hugo/NetBeansProjects/luciajasper/dist/lib"
ARCHIVO_ORIGEN_JAR = "/home/hugo/NetBeansProjects/luciajasper/dist/luciajasper.jar"
RUTA_ORIGEN_REPORTS = "/home/hugo/NetBeansProjects/luciajasper/reports"
RUTA_DESTINO_JASPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jasper")
RUTA_DESTINO_LIB = os.path.join(RUTA_DESTINO_JASPER, "lib")
RUTA_DESTINO_REPORTS = os.path.join(RUTA_DESTINO_JASPER, "reports")

def copiar_archivos_jasper():
    """Copia la carpeta lib, el archivo JAR y la carpeta reports a la carpeta jasper del proyecto."""

    # 1. Crear la carpeta jasper si no existe
    if not os.path.exists(RUTA_DESTINO_JASPER):
        os.makedirs(RUTA_DESTINO_JASPER)
        print(f"Carpeta '{RUTA_DESTINO_JASPER}' creada.")
    else:
        print(f"Carpeta '{RUTA_DESTINO_JASPER}' ya existe.")

    # 2. Copiar la carpeta lib
    if os.path.exists(RUTA_ORIGEN_LIB):
        if os.path.exists(RUTA_DESTINO_LIB):
            try:
                shutil.rmtree(RUTA_DESTINO_LIB)
                print(f"Carpeta '{RUTA_DESTINO_LIB}' existente eliminada.")
            except OSError as e:
                print(f"Error al eliminar '{RUTA_DESTINO_LIB}': {e}")
                return

        try:
            shutil.copytree(RUTA_ORIGEN_LIB, RUTA_DESTINO_LIB)
            print(f"Carpeta '{RUTA_ORIGEN_LIB}' copiada a '{RUTA_DESTINO_LIB}'.")
        except OSError as e:
            print(f"Error al copiar '{RUTA_ORIGEN_LIB}' a '{RUTA_DESTINO_LIB}': {e}")
            return
    else:
        print(f"La carpeta de origen '{RUTA_ORIGEN_LIB}' no existe.")

    # 3. Copiar el archivo JAR
    if os.path.exists(ARCHIVO_ORIGEN_JAR):
        try:
            shutil.copy2(ARCHIVO_ORIGEN_JAR, RUTA_DESTINO_JASPER)
            print(f"Archivo '{ARCHIVO_ORIGEN_JAR}' copiado a '{RUTA_DESTINO_JASPER}'.")
        except OSError as e:
            print(f"Error al copiar '{ARCHIVO_ORIGEN_JAR}' a '{RUTA_DESTINO_JASPER}': {e}")
            return
    else:
        print(f"El archivo de origen '{ARCHIVO_ORIGEN_JAR}' no existe.")

    # 4. Copiar la carpeta reports
    if os.path.exists(RUTA_ORIGEN_REPORTS):
        if os.path.exists(RUTA_DESTINO_REPORTS):
            try:
                shutil.rmtree(RUTA_DESTINO_REPORTS)
                print(f"Carpeta '{RUTA_DESTINO_REPORTS}' existente eliminada.")
            except OSError as e:
                print(f"Error al eliminar '{RUTA_DESTINO_REPORTS}': {e}")
                return
        try:
            shutil.copytree(RUTA_ORIGEN_REPORTS, RUTA_DESTINO_REPORTS)
            print(f"Carpeta '{RUTA_ORIGEN_REPORTS}' copiada a '{RUTA_DESTINO_REPORTS}'.")
        except OSError as e:
            print(f"Error al copiar '{RUTA_ORIGEN_REPORTS}' a '{RUTA_DESTINO_REPORTS}': {e}")
            return
    else:
        print(f"La carpeta de origen '{RUTA_ORIGEN_REPORTS}' no existe.")

if __name__ == "__main__":
    copiar_archivos_jasper()
    print("Proceso de copia completado.")

