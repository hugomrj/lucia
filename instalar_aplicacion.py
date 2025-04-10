import subprocess
import os
from pathlib import Path


'''
export SERVER_NAME="IP"
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
    subprocess.run(cmd, shell=True, check=True, **kwargs)

def main():
    print("🔧 Iniciando despliegue del proyecto Lucia...")

    run("sudo mkdir -p /srv/python")

    # 1. Eliminar versión anterior del proyecto si existe
    if PROJECT_PATH.exists():
        print(f"🗑️ Eliminando proyecto anterior en {PROJECT_PATH}...")
        run(f"sudo rm -rf {PROJECT_PATH}")

    # 2. Clonar el repositorio desde GitHub
    print("📥 Clonando proyecto desde GitHub...")
    run("cd /srv/python && git clone https://github.com/hugomrj/lucia.git")

    # 3. Crear entorno virtual e instalar dependencias
    print("🐍 Creando entorno virtual e instalando dependencias...")
    run(f"python3 -m venv {PROJECT_PATH}/venv")
    run(f"{PROJECT_PATH}/venv/bin/pip install --upgrade pip")
    run(f"{PROJECT_PATH}/venv/bin/pip install -r {PROJECT_PATH}/requirements.txt")

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
    run("sudo systemctl daemon-reexec")
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
