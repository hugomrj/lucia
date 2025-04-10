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
    """Versión mejorada para Python 3.12+"""
    print("🐍 Creando entorno virtual con pip...")
    
    # 1. Limpieza previa
    if venv_path.exists():
        print("🧹 Eliminando entorno virtual existente...")
        run(f"rm -rf {venv_path}")
    
    # 2. Intento principal con las mejores opciones para 3.12
    try:
        print("🔄 Intentando con --upgrade-deps y --clear...")
        run(f"python3.12 -m venv --clear --upgrade-deps {venv_path}")
        
        # Verificación robusta
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            raise subprocess.CalledProcessError(1, "venv")
            
        run(f"{pip_path} --version")
        print("✅ Entorno creado con pip (método optimizado)")
        return
        
    except subprocess.CalledProcessError:
        print("⚠️ Método optimizado falló, probando alternativa...")
    
    # 3. Fallback tradicional con verificación extra
    try:
        run(f"python3.12 -m venv {venv_path}")
        
        # Verificar que python funciona en el venv
        run(f"{venv_path}/bin/python --version")
        
        # Instalación forzada de pip
        run(f"{venv_path}/bin/python -m ensurepip --upgrade")
        run(f"{venv_path}/bin/python -m pip install --upgrade pip")
        
        # Verificación final
        run(f"{venv_path}/bin/pip --version")
        print("✅ Entorno creado (método tradicional)")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error crítico: {str(e)}")
        print("💡 Posibles soluciones:")
        print("1. Verifica que python3.12-venv esté instalado")
        print("2. Prueba con: sudo apt install --reinstall python3.12-venv")
        print("3. Revisa permisos en: /srv/python/lucia")
        sys.exit(1)



def install_pip(venv_path):
    """Instalar pip en el entorno virtual con múltiples estrategias."""
    pip_path = venv_path / "bin" / "pip"
    python_path = venv_path / "bin" / "python"
    
    # Estrategia 1: Verificar si pip ya existe
    if pip_path.exists():
        try:
            run(f"{pip_path} --version")
            print("✅ pip ya está instalado y funcionando.")
            return
        except subprocess.CalledProcessError:
            print("⚠️ pip existe pero no funciona, reinstalando...")
    
    # Estrategia 2: Usar ensurepip
    print("🔧 Intentando instalar pip con ensurepip...")
    try:
        run(f"{python_path} -m ensurepip --upgrade")
        run(f"{python_path} -m pip install --upgrade pip")
        run(f"{pip_path} --version")
        print("✅ pip instalado correctamente con ensurepip.")
        return
    except subprocess.CalledProcessError:
        print("⚠️ Falló ensurepip, probando alternativa...")
    
    # Estrategia 3: Instalación manual de pip
    print("🔧 Intentando instalación manual de pip...")
    try:
        run(f"{python_path} -m pip install --upgrade pip")
        run(f"{pip_path} --version")
        print("✅ pip instalado manualmente.")
        return
    except subprocess.CalledProcessError:
        print("❌ No se pudo instalar pip después de varios intentos.")
        
        # Solución radical: recrear el entorno virtual
        print("🔄 Recreando entorno virtual...")
        run(f"rm -rf {venv_path}")
        run(f"python3 -m venv {venv_path}")
        
        # Intentar nuevamente con ensurepip
        try:
            run(f"{venv_path}/bin/python -m ensurepip --upgrade")
            run(f"{venv_path}/bin/python -m pip install --upgrade pip")
            print("✅ pip instalado después de recrear el entorno.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error crítico: No se pudo instalar pip. Detalles: {e}")
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