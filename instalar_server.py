import os
import subprocess
import getpass

def run_command(command, sudo=False):
    """Ejecuta un comando en el sistema."""
    if sudo:
        command = f"sudo {command}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error al ejecutar {command}: {stderr.decode()}")
    else:
        print(f"Salida: {stdout.decode()}")

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
    """Instala MySQL 8 en Ubuntu."""
    print("Instalando MySQL 8...")
    run_command("apt update", sudo=True)
    run_command("apt install -y mysql-server", sudo=True)
    print("MySQL 8 instalado correctamente.")
    
    # Configurar MySQL
    root_password = getpass.getpass(prompt="Introduce la contraseña para el usuario root de MySQL: ")
    
    print("Configurando MySQL...")
    # Iniciar el proceso de configuración
    run_command(f"sudo mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{root_password}';\"", sudo=True)
    run_command(f"sudo mysql -e \"FLUSH PRIVILEGES;\"", sudo=True)
    print("MySQL configurado correctamente.")

def main():
    """Función principal que coordina la instalación."""
    print("Iniciando la instalación del servidor...")
    install_nginx()
    install_openjdk()
    install_mysql()
    print("Instalación completada.")

if __name__ == "__main__":
    main()
