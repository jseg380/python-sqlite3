from os import name
import sqlite3

#··············································································
# Funciones

# Manipular de BBDD

def crear_conexion(ruta):
    conexion = None
    try:
        conexion = sqlite3.connect(ruta)
    except sqlite3.Error as e:
        print(f"Ha ocurrido el error {e} intentando conectarse a la base de datos")
        exit(1)

    return conexion


def ejecutar_query(conexion, query):
    cursor = conexion.cursor()
    try:
        cursor.execute(query)
        return True
    except sqlite3.Error as e:
        return (e,)


def ejecutar_query_lectura(conexion, query):
    cursor = conexion.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        return (e,)


def cerrar_conexion(conexion):
    conexion.cursor().close()


# Específicas del seminario

# Todas las sentencias deben terminar con ";" para que funcione correctamente
def ejecutar(funcion, conexion, query=None):
    if query != None:
        salidas = []
        queries = query.split(";")[:-1]
        for q in queries:
            salidas.append(funcion(conexion, q))
        
        for i, s in enumerate(salidas):
            if type(s) == tuple:
                print(f"Error al tratar de ejecutar {queries[i]}: {s}")
                return

        return salidas
    else:
        salida = funcion(conexion)
        if type(salida) == tuple:
            print(f"Error al tratar de ejecutar la función {funcion.__name__}: {salida}")
            return

        return salida


def crear_tablas(conexion):
    return ejecutar(ejecutar_query,
                    conexion,
                    """
                    CREATE TABLE IF NOT EXISTS Stock(
                    Cproducto INTEGER PRIMARY KEY AUTOINCREMENT,
                    Cantidad INTEGER DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS Pedido(
                    Cpedido INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ccliente INTEGER,
                    FechaPedido TEXT
                    );

                    CREATE TABLE IF NOT EXISTS DetallePedido(
                    Cpedido INTEGER,
                    Cproducto INTEGER,
                    Cantidad INTEGER DEFAULT 0,
                    PRIMARY KEY(Cproducto,Cpedido),
                    FOREIGN KEY(Cpedido) REFERENCES Stock(Cpedido),
                    FOREIGN KEY(Cproducto) REFERENCES Stock(Cproducto)
                    );
                    """)


def borrar_tablas(conexion):
    return ejecutar(ejecutar_query,
                    conexion,
                    """
                    DROP TABLE IF EXISTS Stock;
                    DROP TABLE IF EXISTS Pedido;
                    DROP TABLE IF EXISTS DetallePedido;
                    """)


def inserta_valores(conexion):
    return ejecutar(ejecutar_query,
                    conexion,
                    """
                    INSERT INTO Stock (Cantidad) VALUES (200);
                    INSERT INTO Stock (Cantidad) VALUES (100);
                    INSERT INTO Stock (Cantidad) VALUES (80);
                    INSERT INTO Stock (Cantidad) VALUES (150);
                    INSERT INTO Stock (Cantidad) VALUES (50);
                    INSERT INTO Stock (Cantidad) VALUES (160);
                    INSERT INTO Stock (Cantidad) VALUES (90);
                    INSERT INTO Stock (Cantidad) VALUES (110);
                    INSERT INTO Stock (Cantidad) VALUES (120);
                    INSERT INTO Stock (Cantidad) VALUES (75);
                    """
                    )


# Función auxiliar de mostrar_tablas
def formatear(tabla, anchura, columnas, titulo, cabeceras):
    anc = anchura
    cols = columnas
    msg = ""
    msg += f'{{:^{anc*cols}}}'.format(titulo.upper()) + "\n"
    msg += "-" * (anc*cols) + "\n"
    msg += (f'{{:>{anc}}}'*cols).format(*cabeceras) + "\n"
    for fila in tabla:
        msg += (f'{{:>{anc}}}'*cols).format(*fila) + "\n"

    return msg


def mostrar_tablas(conexion):
    datos = ejecutar(ejecutar_query_lectura,
                     conexion,
                     """
                     SELECT * FROM Stock;
                     SELECT * FROM Pedido;
                     SELECT * FROM DetallePedido;
                     """)
    stock, pedido, detallePedido = datos
    
    # Stock
    stock_msg = formatear(stock, 12, 2, "stock", ("Cproducto", "Producto"))

    # Pedido
    pedido_msg = formatear(pedido, 12, 3, "pedido", ("Cpedido", "Ccliente", "Fecha"))

    # DetallePedido
    detalle_msg = formatear(detallePedido, 12, 3, "detalle-pedido", ("Cpedido", "Cproducto", "Cantidad"))
    
    messages = [stock_msg, pedido_msg, detalle_msg]

    max_altura = max(stock_msg.count('\n'), pedido_msg.count('\n'), detalle_msg.count('\n'))
    separacion = " " * 4 + "\n"
    separacion = separacion * max_altura

    # Teoricamente debería haber tantas filas en DetallePedido como en Pedido
    # pero si por algún motivo DetallePedido tuviese más, el formato no sería
    # el deseado, además de que no se podrían cambiar las columnas de orden,
    # poniendo, por ejemplo, la columna de Stock al final o en medio, pero
    # rellenando con espacios en blancos sí se puede hacer y no sucede el 
    # problema anteriormente mencionado
    for i, m in enumerate(messages):
        altura = m.count('\n')
        anchura = len(m.split('\n')[0])
        if altura < max_altura:
            fill = " " * anchura + "\n"
            fill = fill * (max_altura - altura)
            messages[i] = m + fill

    # Concatenating multiline strings horizontally
    lineas = zip(messages[0].split('\n'),
                 separacion.split('\n'),
                 messages[1].split('\n'),
                 separacion.split('\n'),
                 messages[2].split('\n'))
    
    msg = '\n'.join([a + b + c + d + e for a, b, c, d, e in lineas])
    
    print(msg)
    

# Menus

def menu_alta(conexion, cod_cliente, fecha):
    opcion = -1
    while opcion < 1 or opcion > 4:
        opcion = int(input("Menú alta de pedido:\n\
1. Añadir detalle de producto\n\
2. Eliminar todos los detalles de producto\n\
3. Cancelar pedido\n\
4. Finalizar pedido\n\
Tu elección: "))
    print()

    cod_articulo = -1
    cod_pedido = ejecutar(ejecutar_query_lectura, conexion,
        f"SELECT Cpedido FROM Pedido WHERE Ccliente = {cod_cliente} AND FechaPedido = \"{fecha}\";")[0][-1][0]

    match opcion:
        case 1:
            cod_articulo = int(input("Introduce código del producto (número entero): "))
            cantidad_producto = ejecutar(ejecutar_query_lectura, conexion, 
                    f"SELECT Cantidad FROM Stock WHERE Cproducto = {cod_articulo};")[0][0][0]

            if cantidad_producto == 0:
                print(f"No existe producto con código: {cod_articulo}")
            else:
                global cantidad
                cantidad = int(input("Introduce cantidad de producto: "))

                if cantidad > cantidad_producto:
                    print(f"El producto con código {cod_articulo} no existe")
                else:
                    ejecutar(ejecutar_query, conexion,
                        f"INSERT INTO DetallePedido (Cpedido, Cproducto, Cantidad) VALUES {cod_pedido, cod_articulo, cantidad};")
                    ejecutar(ejecutar_query, conexion,
                        f"UPDATE Stock SET Cantidad = {cantidad_producto - cantidad} WHERE Cproducto = {cod_articulo};")

                    print("Detalle añadido")
        case 2:
            if cod_articulo == -1:
                ejecutar(ejecutar_query, conexion,
                         f"DELETE FROM DetallePedido WHERE Cpedido = {cod_pedido} AND Cproducto = {cod_articulo};")
                print("Datos del detalle eliminados")
            else:
                print("No se han insertado detalles de pedido")
        case 3:
            ejecutar(ejecutar_query, conexion,
                     f"DELETE FROM DetallePedido WHERE Cpedido = {cod_pedido} AND Cproducto = {cod_articulo};")
            ejecutar(ejecutar_query, conexion,
                     f"DELETE FROM Pedido WHERE Cpedido = {cod_pedido};")
            print("Pedido cancelado")
            return False
        case 4:
            try:
                cantidad in globals()
                conexion.commit()
                print("El pedido fue registrado correctamente")
                return False
            except NameError as e:
                print("No se han rellenado los detalles del pedido")
    
    print()

    return True


def menu(conexion):
    opcion = -1
    while opcion < 1 or opcion > 4:
        opcion = int(input("Menú:\n\
1. Borrar y crear tablas de nuevo (con valores por defecto)\n\
2. Dar de alta nuevo pedido\n\
3. Mostrar contenidos de las tablas\n\
4. Salir del programa y cerrar conexion\n\
Tu elección: "))
    print()
    
    match opcion:
        case 1:
            ejecutar(borrar_tablas, conexion)
            ejecutar(crear_tablas, conexion)
            ejecutar(inserta_valores, conexion)
            print("Tablas reseteadas")
            conexion.commit()
        case 2:
            cod_cliente = int(input("Introduce código de cliente (DNI sin letra): "))
            fecha = input("Introduce fecha de pedido [DD/MM/YYYY]: ")
            ejecutar(ejecutar_query, conexion, 
                f"INSERT INTO Pedido (Ccliente, \"FechaPedido\") VALUES ({cod_cliente}, \"{fecha}\");")

            print()
            seguir = menu_alta(conexion, cod_cliente, fecha)
            while seguir:
                seguir = menu_alta(conexion, cod_cliente, fecha)
        case 3:
            ejecutar(mostrar_tablas, conexion)
        case 4:
            ejecutar(cerrar_conexion, conexion)
            return False
    
    return True

#··············································································
# Main

def main():
    conexion = crear_conexion('seminario1.sqlite3')

    ejecutar(crear_tablas, conexion)
    
    opcion = True
    while opcion:
        opcion = menu(conexion)
        print()
    
    print("Fin del programa")


if __name__ == "__main__":
    main()
