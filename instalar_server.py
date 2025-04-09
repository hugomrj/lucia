import os
import subprocess
import getpass


'''
export MYSQL_ROOT_PASSWORD="TuContraseñaSegura"
python3 instalar_server.py
'''


def run_command(command, sudo=False):
    """Ejecuta un comando en el sistema y muestra la salida en tiempo real."""
    if sudo:
        command = f"sudo {command}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        print(line, end='')

    process.wait()
    if process.returncode != 0:
        print(f"\nError al ejecutar {command} (código {process.returncode})")


def configure_swap(size_gb=4):
    """Configura el archivo de swap."""
    swapfile_path = "/swapfile"
    print(f"Creando archivo de swap de {size_gb}GB...")
    
    # Crear archivo de swap
    run_command(f"dd if=/dev/zero of={swapfile_path} bs=1M count={size_gb * 1024} status=progress", sudo=True)
    run_command(f"mkswap {swapfile_path}", sudo=True)
    run_command(f"swapon {swapfile_path}", sudo=True)

    # Agregar la entrada de swap en fstab
    with open("/etc/fstab", "a") as fstab:
        fstab.write(f"{swapfile_path} none swap sw 0 0\n")
    print("Swap configurado correctamente.")


def install_nginx():
    """Instala Nginx en Ubuntu."""
    print("Instalando Nginx...")
    run_command("apt update", sudo=True)
    run_command("apt install -y nginx", sudo=True)
    print("Nginx instalado correctamente.")

def install_openjdk():
    """Instala OpenJDK 21 en Ubuntu."""
    print("Instalando OpenJDK 21...")
    run_command("apt install -y openjdk-21-jdk", sudo=True)
    print("OpenJDK 21 instalado correctamente.")

def install_mysql():
    """Instala MySQL 8 en Ubuntu y configura una contraseña para el usuario root."""
    print("Instalando MySQL 8...")
    run_command("apt update", sudo=True)
    run_command("apt install -y mysql-server", sudo=True)
    print("MySQL 8 instalado correctamente.")
    
    # Leer la contraseña de la variable de entorno
    root_password = os.getenv("MYSQL_ROOT_PASSWORD")
    
    if not root_password:
        print("Error: La variable de entorno MYSQL_ROOT_PASSWORD no está configurada.")
        return

    print("Configurando MySQL...")
    
    # Ejecutar las instrucciones para establecer la contraseña del root y asegurar MySQL
    run_command(f"sudo mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{root_password}';\"", sudo=True)
    run_command("sudo mysql -e \"FLUSH PRIVILEGES;\"", sudo=True)
    
    print("MySQL configurado correctamente.")

def main():
    """Función principal que coordina la instalación."""
    print("Iniciando la instalación del servidor...")
    configure_swap(size_gb=4)  # Configura el swap de 4GB
    install_nginx()
    install_openjdk()
    install_mysql()
    print("Instalación completada.")

if __name__ == "__main__":
    main()
