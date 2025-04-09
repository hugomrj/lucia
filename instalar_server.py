import os
import subprocess
import getpass

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
    """Configura el swap en el sistema si no está configurado o si se desea cambiar el tamaño."""
    print(f"Verificando y configurando swap de {size_gb}GB...")
    # Verificar si ya existe un archivo de swap
    result = subprocess.run("swapon --show", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stdout:
        print("Swap ya está configurado.")
    else:
        # Crear un archivo de swap de 4GB
        print("Creando archivo de swap...")
        run_command(f"sudo fallocate -l {size_gb}G /swapfile", sudo=True)
        run_command("sudo chmod 600 /swapfile", sudo=True)
        run_command("sudo mkswap /swapfile", sudo=True)
        run_command("sudo swapon /swapfile", sudo=True)
        # Hacer permanente el swap editando fstab
        with open("/etc/fstab", "a") as fstab:
            fstab.write("\n/swapfile none swap sw 0 0\n")
        print(f"Swap de {size_gb}GB configurado correctamente.")

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
    configure_swap(size_gb=4)  # Configura el swap de 4GB
    install_nginx()
    install_openjdk()
    install_mysql()
    print("Instalación completada.")

if __name__ == "__main__":
    main()
