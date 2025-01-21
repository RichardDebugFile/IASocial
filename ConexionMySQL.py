import mysql.connector
from mysql.connector import Error


class ConexionMySQL:
    def __init__(self, host="localhost", user="root", password="", database="iasocial"):
        """
        Inicializa la conexión a la base de datos MySQL.
        :param host: Dirección del servidor MySQL (por defecto 'localhost').
        :param user: Usuario de la base de datos (por defecto 'root').
        :param password: Contraseña del usuario (por defecto '').
        :param database: Nombre de la base de datos (por defecto 'IASocial').
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def conectar(self):
        """
        Establece la conexión con la base de datos.
        """
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.conn.is_connected():
                self.cursor = self.conn.cursor()
                print("Conexión exitosa a la base de datos.")
        except Error as e:
            print(f"Error al conectar con la base de datos: {e}")

    def ejecutar_consulta(self, query, parametros=None):
        """
        Ejecuta una consulta SQL.
        :param query: Consulta SQL a ejecutar.
        :param parametros: Parámetros para la consulta (opcional).
        :return: Resultado de la consulta si es una SELECT, None de lo contrario.
        """
        try:
            if self.cursor:
                self.cursor.execute(query, parametros)
                if query.strip().upper().startswith("SELECT"):
                    return self.cursor.fetchall()
                else:
                    self.conn.commit()
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")

    def cerrar_conexion(self):
        """
        Cierra la conexión con la base de datos.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Conexión cerrada correctamente.")
