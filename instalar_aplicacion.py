import subprocess
import os
import sys
from pathlib import Path
import time

'''
sudo SERVER_NAME="IP" python3 lucia/instalar_aplicacion.py
'''

# Ruta donde se instalará el proyecto
PROJECT_PATH = Path("/srv/python/lucia")

# Obtener nombre del servidor desde variable de entorno
SERVER_NAME = os.environ.get("SERVER_NAME")
if not SERVER_NAME:
    raise ValueError("⚠️ La variable de entorno SERVER_NAME no está definida. Usá: export SERVER_NAME=tu.dominio.com")

def run(cmd, **kwargs):
    """Ejecuta un comando de shell y muestra lo que se está haciendo."""
    print(f"\n==> Ejecutando: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar: {cmd}")
        print(f"Error: {e}")
        sys.exit(1)

def check_and_install_venv():
    """Verifica si python3-venv está instalado, y si no lo está, lo instala."""
    try:
        subprocess.run("python3 -m venv --help", shell=True, check=True, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ python3-venv ya está instalado.")
    except subprocess.CalledProcessError:
        print("⚠️ python3-venv no está instalado. Instalando...")
        run("sudo apt update")
        run("sudo apt install -y python3-venv")

def create_virtualenv(venv_path):
    """Crea un entorno virtual con reintentos si falla."""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"Intentando crear entorno virtual (intento {attempt}/{max_attempts})...")
        try:
            run(f"python3 -m venv {venv_path}")
            # Verificar que se crearon los archivos esenciales
            if (venv_path / "bin" / "python").exists():
                print("✅ Entorno virtual creado correctamente.")
                return
            else:
                print("⚠️ El entorno virtual no se creó completamente.")
                raise subprocess.CalledProcessError(1, "venv")
        except subprocess.CalledProcessError:
            if attempt < max_attempts:
                print("⚠️ Falló la creación del entorno virtual. Reintentando...")
                time.sleep(2)
                # Eliminar el directorio si existe para un intento limpio
                run(f"rm -rf {venv_path}")
            else:
                print("❌ No se pudo crear el entorno virtual después de varios intentos.")
                sys.exit(1)

def install_pip(venv_path):
    """Instalar pip en el entorno virtual con reintentos."""
    pip_path = venv_path / "bin" / "pip"
    python_path = venv_path / "bin" / "python"  # Esta es la línea corregida
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            if not pip_path.exists():
                print(f"Instalando pip (intento {attempt}/{max_attempts})...")
                run(f"{python_path} -m ensurepip --upgrade")
                run(f"{python_path} -m pip install --upgrade pip")
            
            # Verificar que pip funciona
            run(f"{pip_path} --version")
            print("✅ pip instalado correctamente.")
            return
        except subprocess.CalledProcessError:
            if attempt < max_attempts:
                print("⚠️ Falló la instalación de pip. Reintentando...")
                time.sleep(2)
            else:
                print("❌ No se pudo instalar pip después de varios intentos.")
                sys.exit(1)

def main():
    print("🔧 Iniciando despliegue del proyecto Lucia...")

    check_and_install_venv()

    run("sudo mkdir -p /srv/python")
    run(f"sudo chown {os.getlogin()}:{os.getlogin()} /srv/python")

    # 1. Eliminar versión anterior del proyecto si existe
    if PROJECT_PATH.exists():
        print(f"🗑️ Eliminando proyecto anterior en {PROJECT_PATH}...")
        run(f"rm -rf {PROJECT_PATH}")

    # 2. Clonar el repositorio desde GitHub
    print("📥 Clonando proyecto desde GitHub...")
    run("cd /srv/python && git clone https://github.com/hugomrj/lucia.git")

    # 3. Crear entorno virtual e instalar dependencias
    print("🐍 Creando entorno virtual e instalando dependencias...")
    venv_path = PROJECT_PATH / "venv"
    create_virtualenv(venv_path)
    install_pip(venv_path)
    
    # Instalar dependencias
    run(f"{venv_path}/bin/pip install --upgrade pip")
    run(f"{venv_path}/bin/pip install -r {PROJECT_PATH}/requirements.txt")

    # 4. Crear servicio systemd para Gunicorn
    print("⚙️ Creando archivo de servicio systemd...")
    lucia_service = f"""[Unit]
Description=Gunicorn instance to serve Lucia
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory={PROJECT_PATH}
Environment="PATH={PROJECT_PATH}/venv/bin"
ExecStart={PROJECT_PATH}/venv/bin/gunicorn --workers 3 --bind unix:{PROJECT_PATH}/lucia.sock wsgi:app

[Install]
WantedBy=multi-user.target
"""
    with open("/tmp/lucia.service", "w") as f:
        f.write(lucia_service)
    run("sudo mv /tmp/lucia.service /etc/systemd/system/lucia.service")

    # 5. Habilitar y reiniciar el servicio
    print("🔁 Activando servicio lucia...")
    run("sudo systemctl daemon-reload")
    run("sudo systemctl enable lucia")
    run("sudo systemctl restart lucia")

    # 6. Configurar Nginx
    print("🌐 Configurando Nginx...")
    nginx_conf = f"""server {{
    listen 80;
    server_name {SERVER_NAME};

    location / {{
        include proxy_params;
        proxy_pass http://unix:{PROJECT_PATH}/lucia.sock;
    }}
}}
"""
    with open("/tmp/lucia", "w") as f:
        f.write(nginx_conf)
    run("sudo mv /tmp/lucia /etc/nginx/sites-available/lucia")
    run("sudo ln -sf /etc/nginx/sites-available/lucia /etc/nginx/sites-enabled/lucia")
    run("sudo nginx -t")
    run("sudo systemctl reload nginx")

    print("\n✅ Despliegue finalizado correctamente.")

if __name__ == '__main__':
    main()