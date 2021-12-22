"""
Desarrollado por: Ing. Ricardo Celedon
Maracaibo, Venezuela, 12-3-2021
zeytips@gmail.com
"""

import mysql.connector
import PySimpleGUI as sg # GUI Framework
import re # Regular expressions to filter filenames
# import pickle # Module for saving data in binary streams
from datetime import datetime, timedelta # datetime to get curent date, timedelta to substract days from a date

hostname = 'localhost'
username = 'root'
password = ''

myConnection = mysql.connector.connect(host=hostname, user=username, passwd=password)
mycursor = myConnection.cursor()

# def doQuery(conn, query):
#     cur = conn.cursor()
#     cur.execute(query)
#     # cur.
#     print(cur.fetchall())

# doQuery(myConnection, "SELECT name,lname FROM clients")
# myConnection.close()

sg.theme('Reddit') # SystemDefaultForReal

#VARIABLES
version = "0.4a" # Version number
todayDay = datetime.today().strftime('%Y-%m-%d') # Starting variable for today date match

# GUI variables

# Database headers
inventario_h = []
servicios_h = []
bitacoras_h = []
clientes_h = []

# 'bitacoras',), ('clientes',), ('company_info',), ('inventario',), ('inventario_uses_servicios',), ('servicios'
# Database data
companyName = ''
inventario = []
servicios = []
bitacoras = []
clientes = []

dbName = ''

def parenth(listItems, quotes):
    outputString = "("
    for i in range(0, len(listItems)):
        if i != len(listItems) - 1:
            outputString += quotes + str(listItems[i]) + quotes + ", "
        else:
            outputString += quotes + str(listItems[i]) + quotes + ")"
    return outputString


# Starting Load database

def recoverItems(tablename):
    result = []
    result_h = []
    mycursor.execute("SELECT * FROM " + tablename)
    tableRawList = mycursor.fetchall()
    mycursor.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = '" + tablename + "' and table_schema = '" + dbName + "'")
    table_hRawList = mycursor.fetchall()
    for items in tableRawList:
        tempArray = []
        for atom in range(0, len(items)):
            tempArray.append(str(items[atom]))
        result.append(tempArray)
    for atom_h in table_hRawList:
        result_h.append(atom_h[0])

    return result, result_h

def callClients():
    mycursor.execute("SELECT id_cliente,nombre,apellido FROM clientes")
    clientesRawList = mycursor.fetchall()
    clientesList = []
    for cli in clientesRawList:
        nombre = ''
        for item in range(0, len(cli)):
            if item == 0:
                nombre += str(cli[item]) + ":"
            else:
                nombre += " " + cli[item]
        clientesList.append(nombre)
    return clientesList

def callServices():
    mycursor.execute("SELECT id_servicio,servicio,nombre FROM servicios JOIN clientes ON servicios.cliente_id=clientes.id_cliente WHERE servicios.cliente_id=clientes.id_cliente")
    serviciosRawList = mycursor.fetchall()
    serviciosList = []
    for serv in serviciosRawList:
        nombre = ''
        for item in range(0, len(serv)):
            if item == 0:
                nombre += str(serv[item]) + ":"
            else:
                nombre += " " + serv[item]
        serviciosList.append(nombre)
    return serviciosList

invalid_db = True # Flag for invalid file / Non existent



# source_filename = values[0]
# print(source_filename)

match sg.popup_yes_no('Desea abrir una compañia existente?\n\nOprima "No" para crear nueva'):
    case 'Yes': # Get popup result
        while not dbName or invalid_db: # While dbFilePath is Null and invalid_file flag is True
            # dbFilePath = sg.popup_get_file('Cargar archivo de compañia:', file_types=(("BinnaCele Data File", "*.bdata"), ("All file types", "*.*")))
            mycursor.execute("SHOW DATABASES")
            dbRawList = mycursor.fetchall()
            dbList = []
            for x in dbRawList:
                # print(x[0])
                if not x[0] in('information_schema', 'mysql', 'performance_schema', 'phpmyadmin'):
                    dbList.append(x[0])
                # print(dbList)
            event, values = sg.Window('Bases de datos', [[sg.Text('Escoja la base de datos de lista:')],
                                                           [sg.Table(dbList, ['Databases'], justification='left', auto_size_columns=False, col_widths=[30])],
                                                           [sg.Button('Abrir'), sg.Button('Salir')]]).read(close=True)

            if event in ('Salir', None): # If Cancel or close window, exit program
                exit(0)
            elif values[0]:
                dbName = dbList[values[0][0]]
                mycursor.execute("USE " + dbName)
                mycursor.execute("SHOW TABLES")
                if mycursor.fetchall() == [('bitacoras',), ('clientes',), ('company_info',), ('inventario',), ('inventario_uses_servicios',), ('servicios',)]:
                    mycursor.execute("SELECT * FROM company_info")
                    companyName = mycursor.fetchone()[0]


                    bitacoras, bitacoras_h = recoverItems('bitacoras')
                    clientes, clientes_h = recoverItems('clientes')
                    inventario, inventario_h = recoverItems('inventario')
                    servicios, servicios_h = recoverItems('servicios')

                    callServices()

                    # print(bitacoras)
                    # print(bitacoras_h)
                    invalid_db = False
                else:
                    sg.popup_error("La base de datos seleccionada no es valida para esta aplicacion.\n\nPor favor seleccione una base de datos valida.")

    case 'No':
        while not companyName or invalid_db: # While name is empty
            companyName = sg.popup_get_text('Ingrese el nombre de su compañia')
            match companyName:
                case None: # If Cancel or close window: exit program
                    exit(0)
                case '':
                    sg.popup_error('ERROR: Por favor ingrese un nombre de compañia')
                case _:
                    dbName = re.sub(r"[^a-zA-Z0-9]+", "", companyName.lower())  # re.sub removes all characters that are not a-z or 0-9
                    mycursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '" + dbName + "'")
                    testIfExists = mycursor.fetchall()
                    if testIfExists:
                        sg.popup_error('ERROR: Ya existe una base de datos con ese nombre.\n\nPor favor elija otro nombre o use dicha base de datos.')
                    else:
                        mycursor.execute("CREATE DATABASE " + dbName)
                        mycursor.execute("USE " + dbName)
                        mycursor.execute("CREATE TABLE company_info (company_name VARCHAR(40))")
                        mycursor.execute("CREATE TABLE clientes (id_cliente INT PRIMARY KEY AUTO_INCREMENT, dni VARCHAR(10), nombre VARCHAR(20), apellido VARCHAR(20), correo VARCHAR(20), telefono VARCHAR(15), direccion VARCHAR(50))")
                        mycursor.execute("CREATE TABLE servicios (id_servicio INT PRIMARY KEY AUTO_INCREMENT, servicio VARCHAR(20), departamento VARCHAR(15), tiempo INT (3), precio DECIMAL(8,2), costo DECIMAL(8,2), fecha DATE, cliente_id INT REFERENCES clientes(id_cliente))")
                        mycursor.execute("CREATE TABLE bitacoras (id_bitacora INT PRIMARY KEY AUTO_INCREMENT, problema VARCHAR(45), descripcion VARCHAR(45), solucion VARCHAR(45), causa VARCHAR(45), estado VARCHAR(15), fecha_solicitud DATE, fecha_final DATE, servicios_id INT REFERENCES servicios(id_servicio))")
                        mycursor.execute("CREATE TABLE inventario (id_rubro INT PRIMARY KEY AUTO_INCREMENT, rubro VARCHAR(20), cantidad DECIMAL(8,2), medida VARCHAR(10), precio_nominal DECIMAL(8,2), stock DECIMAL(8,2))")
                        mycursor.execute("CREATE TABLE inventario_uses_servicios (inventario_id INT REFERENCES inventario(id_rubro), servicios_id INT REFERENCES servicios(id_servicio))")
                        mycursor.execute("INSERT INTO company_info VALUES ('" + companyName + "')")
                        myConnection.commit()

                        bitacoras, bitacoras_h = recoverItems('bitacoras')
                        clientes, clientes_h = recoverItems('clientes')
                        inventario, inventario_h = recoverItems('inventario')
                        servicios, servicios_h = recoverItems('servicios')

                        invalid_db = False

    case None:
        exit(0)

# New Item: It creates an element list in the required list
# def newThing(listData, data, header): # listData is for values, data is for Database data name, and header is for database_h headers
#     tempArray = ["{:04}".format(len(data)+1)] # Adding first element as 0001 identifier base on list position
#     for column in range(1, len(header)):
#         tempArray.append(listData[column-1]) # Appending passed data to list variable
#     data.append(tempArray) # Adds temporal array to required data source list

def formatDate(date): # Grab tuples of date like (MM, DD, YYYY)
    new_date = str(date[2]) + "-" + str("{:02}".format(date[0])) + "-" + str("{:02}".format(date[1]))
    return new_date

###
###     balancesWindow functions
###
def dateRange(date_a, date_b): # Arrange dates in correct order a < b. Accepts range in format "YYYY-MM-DD"
    if date_a <= date_b:
        return (date_a, date_b)
    else:
        return(date_b, date_a)

def getBalance(date_s, date_f): # Get balance values for price, cost, utility according to specified dates
    acum_costo = 0
    acum_precio = 0
    date_s, date_f = dateRange(date_s, date_f) # Arrange them properly
    print(date_s, date_f)
    for fila in range(0,len(servicios)):
        if(servicios[fila][servicios_h.index("fecha")] >= date_s and servicios[fila][servicios_h.index("fecha")] <= date_f): # Iterate and adds only those values who are inside the required date range
            acum_precio += float(servicios[fila][servicios_h.index("precio")]) # Add all prices and costs
            acum_costo += float(servicios[fila][servicios_h.index("costo")])
    utilidad_total = acum_precio - acum_costo
    return [acum_precio, acum_costo, utilidad_total] # Return a list

############################################################################################################################################################
# GUI

# FUNCTIONS

def makeMenuWindow():
    layout = [[sg.Text('BinnaCele v' + version, font='Console 14 bold', pad=[[0, 0], [0, 25]])],
                  [sg.Text('Compañia: ' + companyName, font='Console 10 bold')],
                  [sg.Button('Informacion de Balance', size=(18, 1), key='balance')],
                  [sg.Button('Registro de Servicios', size=(18, 1), key='servicios')],
                  [sg.Button('Inventario', size=(18, 1))],
                  [sg.Button('Registro de Bitacoras', size=(18, 1), key='bitacoras')],
                  [sg.Button('Registro de Clientes', size=(18, 1), key='clientes')],
                  [sg.Button('Salir', pad=[[230, 0], [40, 0]])]]

    return sg.Window('Menu Principal', layout, element_justification='c', finalize=True)

def makeBalanceWindow():
    resumenLayout = [[sg.Column([[sg.Text('Utilidad total:')], [sg.Text(str(util_view)+'$', key='-UTILIDAD-')]]), sg.Column(
        [[sg.Text('Ventas totales:')], [sg.Text(str(ventas_view)+"$", key='-VENTAS-')], [sg.Text('Gastos totales:')], [sg.Text(str(costos_view)+"$", key='-GASTOS-')]])]]

    layout = [[sg.Button('Diario', key='diario'), sg.Button('Semanal', key='semanal'), sg.Button('Mensual', key='mensual'), sg.Button('Anual', key='anual')],
        [sg.HorizontalSeparator(pad=[20, 20])],
        [sg.Text('Fecha Inicio: ' + todayDay, key='-FECHAI-'), sg.Text('Fecha Final: ' + todayDay, key='-FECHAF-')],
        [sg.Frame('', resumenLayout)],
        [sg.HorizontalSeparator(pad=[20, 20])],
        [sg.Button('Escoger rango de fechas', pad=[[0, 0], [20, 0]], key='chooserange')],
        [sg.Button('Salir', pad=[[230, 0], [0, 0]])]]

    return sg.Window('Balance', layout, modal=True, element_justification='c', finalize=True, size=[350,350])

def makeServicesWindow():
    # "servicio", "departamento", "precio", "costo", "tiempo", "fecha"

    formLayout = [[sg.Frame('Servicio', [[sg.Input(size=[25,1], key='-SERVICE-')]]), sg.Frame('Departamento', [[sg.InputCombo(("Telefonia", "Electrodomesticos", "Informatica", "Ciberseguridad"), default_value='Telefonia', key='-DPTO-', readonly=True)]]), sg.Frame('Tiempo', [[sg.Input(size=[10,1], key='-TIME-')]]), sg.Frame('Precio ($)', [[sg.Input(size=[5,1], key='-PRICE-')]]), sg.Frame('Costo ($)', [[sg.Input(size=[5,1], key='-COST-')]])],
                  [sg.Frame('Fecha', [[sg.Input(key='-FECHA-', disabled=True, size=[15,1], default_text=datetime.today().strftime('%Y-%m-%d')), sg.Button('Escoger fecha', key='fecha')]]), sg.Frame('Cliente', [[sg.InputCombo(callClients(), key='-CLIENT-', readonly=True)]])]]

    layout = [[sg.Frame('Todos:', [[sg.Table(list(servicios), list(servicios_h), key='-SERVICESTABLE-', auto_size_columns=False,)]])],# Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20,20])],
              [sg.Frame('Registro nuevo Servicio:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardar'),sg.Button('Vaciar Campos', key='empty'),sg.Button('Borrar', key='delete')],
              [sg.Button('Salir', pad=[[630, 0], [0, 0]])]]

    return sg.Window('Servicios', layout, finalize=True, modal=True, element_justification='c')

def makeInvWindow():
    # "id_rubro", "rubro", "cantidad", "medida", "precio_nominal", "stock"
    formLayout = [[sg.Frame('Rubro', [[sg.Input(size=[25,1], key='-RUBRO-')]]), sg.Frame('Cantidad', [[sg.Input(size=[5,1], key='-CANTIDAD-')]]), sg.Frame('Medida', [[sg.Input(size=[8,1], key='-MEDIDA-')]])],
                  [sg.Frame('Precio Nominal ($)', [[sg.Input(size=[8,1], key='-PNOMINAL-')]]), sg.Frame('Stock', [[sg.Input(size=[10,1], key='-STOCK-')]])]]


    layout = [[sg.Frame('Existencias:', [[sg.Table(list(inventario), list(inventario_h), key='-INVTABLE-', auto_size_columns=False)]])], # Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20,20])],
              [sg.Frame('Registro nuevo Item:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardarinv'),sg.Button('Vaciar Campos', key='emptyinv'),sg.Button('Borrar', key='deleteinv')],
              [sg.Button('Salir', pad=[[550, 0], [0, 0]])]]

    return sg.Window('Inventario', layout, modal=True, finalize=True, element_justification='c')

def makeBitacorasWindow():
    formLayout = [[sg.Frame('Servicio', [[sg.InputCombo(callServices(), key='-SERVICES-', readonly=True, enable_events=True)]]), sg.Frame('Problema', [[sg.Input(size=[20, 1], key='-PROBLEM-')]]),
                   sg.Frame('Estado', [[sg.Input(size=[10, 1], key='-STATUS-')]]),
                   sg.Frame('Fecha Solicitud', [[sg.Input(key='-FECHABSOL-', disabled=True, size=[15,1]), sg.Button('Escoger fecha', key='fechasol')]]),
                   sg.Frame('Fecha Final', [[sg.Input(key='-FECHABFIN-', disabled=True, size=[15,1], default_text=datetime.today().strftime('%Y-%m-%d')), sg.Button('Escoger fecha', key='fechafin')]])],
                   [sg.Frame('Descripcion', [[sg.Multiline(key='-DESCR-', size=[40,10])]]),
                   sg.Frame('Solucion', [[sg.Multiline(key='-SOL-', size=[40,10])]]),
                   sg.Frame('Causa', [[sg.Multiline(key='-CAUSE-', size=[40,10])]])]]
    # "id_registro", "problema", "descripcion", "solucion", "causa", "sistemas", "estado", "fecha"

    layout = [[sg.Frame('Base de Conocimientos:',
                        [[sg.Table(list(bitacoras), list(bitacoras_h), key='-BINNTABLE-', auto_size_columns=False)]])],
              # Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20, 20])],
              [sg.Frame('Documentacion nueva Bitacora:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardarbinn'), sg.Button('Vaciar Campos', key='emptybinn'),
               sg.Button('Borrar', key='deletebinn')],
              [sg.Button('Salir', pad=[[550, 0], [0, 0]])]]

    return sg.Window('Bitacoras', layout, modal=True, finalize=True, element_justification='c')

def makeClientesWindow():
    # "id_cliente", "dni", "nombre", "apellido", "correo", "telefono", "direccion"
    formLayout = [[sg.Frame('DNI', [[sg.Input(size=[20, 1], key='-DNI-')]]),
                   sg.Frame('Nombre', [[sg.Input(size=[20, 1], key='-FNAME-')]]),
                   sg.Frame('Apellido', [[sg.Input(size=[20, 1], key='-LNAME-')]])],
                  [sg.Frame('Correo', [[sg.Input(size=[25, 1], key='-EMAIL-')]]), sg.Frame('Telefono', [[sg.Input(size=[15, 1], key='-PHONE-')]]), sg.Frame('Direccion', [[sg.Input(size=[20, 1], key='-ADDR-')]])]]

    layout = [[sg.Frame('Clientes:',
                        [[sg.Table(list(clientes), list(clientes_h), key='-CLIENTTABLE-', auto_size_columns=False)]])],
              # Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20, 20])],
              [sg.Frame('Agregar nuevo cliente:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardarcli'), sg.Button('Vaciar Campos', key='emptycli'),
               sg.Button('Borrar', key='deletecli')],
              [sg.Button('Salir', pad=[[550, 0], [0, 0]])]]

    return sg.Window('Clientes', layout, modal=True, finalize=True, element_justification='c')

# Menu Persistent loop

menuWindow, balanceWindow, servicesWindow, invWindow, bitacorasWindow, clientesWindow = makeMenuWindow(), None, None, None, None, None # Needed to have multiple windows

while True:
    window, event, values = sg.read_all_windows()
    print(event, values)
    if window == menuWindow and event in (sg.WIN_CLOSED, 'Salir'):
        break

    # Windows calling/making
    if window == menuWindow:
        match str(event):
            case 'balance':
                ventas_view, costos_view, util_view = getBalance(todayDay, todayDay)
                menuWindow.hide()
                balanceWindow = makeBalanceWindow()
            case 'servicios':
                menuWindow.hide()
                servicesWindow = makeServicesWindow()
            case 'Inventario':
                menuWindow.hide()
                invWindow = makeInvWindow()
            case 'bitacoras':
                menuWindow.hide()
                bitacorasWindow = makeBitacorasWindow()
            case 'clientes':
                menuWindow.hide()
                clientesWindow = makeClientesWindow()
            case _:
                print("[!] ERROR: Unexpected error...")
                exit(1)

    # Closing flows
    if window == balanceWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            balanceWindow.close()
            menuWindow.un_hide()
    if window == servicesWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            servicesWindow.close()
            menuWindow.un_hide()
    if window == invWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            invWindow.close()
            menuWindow.un_hide()
    if window == bitacorasWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            bitacorasWindow.close()
            menuWindow.un_hide()
    if window == clientesWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            clientesWindow.close()
            menuWindow.un_hide()

    # Main GUI version

    # Balance Window events
    if window == balanceWindow:
        if event == 'diario':
            todayDay = datetime.today().strftime('%Y-%m-%d') # Getting current date with format YYYY-MM-DD
            ventas_view, costos_view, util_view = getBalance(todayDay, todayDay)
            window['-UTILIDAD-'].update(str(util_view)+"$")
            window['-GASTOS-'].update(str(costos_view) + "$")
            window['-VENTAS-'].update(str(ventas_view) + "$")
            window['-FECHAI-'].update("Fecha Inicio: " + todayDay)
            window['-FECHAF-'].update("Fecha Final: " + todayDay)
        if event == 'semanal':
            todayDay = datetime.today().strftime('%Y-%m-%d')
            lastWeek = (datetime.today() - timedelta(days=6)).strftime('%Y-%m-%d') # Last 7 days
            ventas_view, costos_view, util_view = getBalance(lastWeek, todayDay)
            window['-UTILIDAD-'].update(str(util_view) + "$")
            window['-GASTOS-'].update(str(costos_view) + "$")
            window['-VENTAS-'].update(str(ventas_view) + "$")
            window['-FECHAI-'].update("Fecha Inicio: " + lastWeek)
            window['-FECHAF-'].update("Fecha Final: " + todayDay)
        if event == 'mensual':
            todayDay = datetime.today().strftime('%Y-%m-%d')
            lastMonth = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d') # Last 31 days
            ventas_view, costos_view, util_view = getBalance(lastMonth, todayDay)
            window['-UTILIDAD-'].update(str(util_view) + "$")
            window['-GASTOS-'].update(str(costos_view) + "$")
            window['-VENTAS-'].update(str(ventas_view) + "$")
            window['-FECHAI-'].update("Fecha Inicio: " + lastMonth)
            window['-FECHAF-'].update("Fecha Final: " + todayDay)
        if event == 'anual':
            todayDay = datetime.today().strftime('%Y-%m-%d')
            lastYear = (datetime.today() - timedelta(days=364)).strftime('%Y-%m-%d') # Last 365 days
            ventas_view, costos_view, util_view = getBalance(lastYear, todayDay)
            window['-UTILIDAD-'].update(str(util_view) + "$")
            window['-GASTOS-'].update(str(costos_view) + "$")
            window['-VENTAS-'].update(str(ventas_view) + "$")
            window['-FECHAI-'].update("Fecha Inicio: " + lastYear)
            window['-FECHAF-'].update("Fecha Final: " + todayDay)
        if event == 'chooserange':
            date_start = formatDate(sg.popup_get_date())
            date_end = formatDate(sg.popup_get_date())
            date_start, date_end = dateRange(date_start, date_end)
            ventas_view, costos_view, util_view = getBalance(date_start, date_end) # Order doesn't matter since there is a function to arrange them rangeDate(date_s, date_f)
            window['-UTILIDAD-'].update(str(util_view) + "$")
            window['-GASTOS-'].update(str(costos_view) + "$")
            window['-VENTAS-'].update(str(ventas_view) + "$")
            window['-FECHAI-'].update("Fecha Inicio: " + date_start)
            window['-FECHAF-'].update("Fecha Final: " + date_end)


# def newThing(listData, data, header):  # listData is for values, data is for Database data name, and header is for database_h headers
#     for column in range(1, len(header)):
#         tempArray.append(listData[column - 1])  # Appending passed data to list variable
#     mycursor.execute("INSERT INTO " + data + "")
    # data.append(tempArray)  # Adds temporal array to required data source list

    # Services Window events
    if window == servicesWindow:
        if event == 'fecha':
            window['-FECHA-'].update(formatDate(sg.popup_get_date()))

        if event == 'guardar':
            listedData = list(values.values())
            listedData.pop(0)
            for i in range(0, len(listedData)):
                if not listedData[i]:
                    sg.popup_error('ERROR: Ingrese valores en las casillas')
                    break
                elif listedData[i] and i == len(listedData) - 1:
                    temp_h = servicios_h[1:8]
                    print(temp_h)
                    mycursor.execute("INSERT INTO servicios" + parenth(temp_h, "") + "VALUES" + parenth(listedData, "'"))
                    myConnection.commit()
                    servicios, servicios_h = recoverItems('servicios')
                    window['-SERVICESTABLE-'].update(values=servicios)

        if event == 'delete':
            delRows = values['-SERVICESTABLE-'] # Rows to be deleted selected by the user and returned by the event
            if delRows: # If not empty
                for index in sorted(delRows, reverse=True):
                    mycursor.execute("DELETE FROM servicios WHERE id_servicio=" + servicios[index][0])
                    myConnection.commit()
                    servicios, servicios_h = recoverItems('servicios')
                    window['-SERVICESTABLE-'].update(values=servicios)

        if event == 'empty':
            window['-SERVICE-'].update('')
            window['-PRICE-'].update('')
            window['-COST-'].update('')
            window['-TIME-'].update('')
            window['-FECHA-'].update('')

    # Inv Window events
    if window == invWindow:
        if event == 'guardarinv':
            listedData = list(values.values())
            listedData.pop(0)
            for i in range(0, len(listedData)):
                if not listedData[i]:
                    sg.popup_error('ERROR: Ingrese valores en las casillas')
                    break
                elif listedData[i] and i == len(listedData) - 1:
                    temp_h = inventario_h[1:6]
                    mycursor.execute("INSERT INTO inventario" + parenth(temp_h, "") + "VALUES" + parenth(listedData, "'"))
                    myConnection.commit()
                    inventario, inventario_h = recoverItems('inventario')
                    window['-INVTABLE-'].update(values=inventario)

        if event == 'deleteinv':
            delRows = values['-INVTABLE-']  # Rows to be deleted selected by the user and returned by the event
            if delRows:  # If not empty
                for index in sorted(delRows, reverse=True):
                    mycursor.execute("DELETE FROM inventario WHERE id_rubro=" + inventario[index][0])
                    myConnection.commit()
                    inventario, inventario_h = recoverItems('inventario')
                    window['-INVTABLE-'].update(values=inventario)
            else:
                print("Nothing selected")
            window['-INVTABLE-'].update(values=inventario)

        if event == 'emptyinv':
            window['-RUBRO-'].update('')
            window['-CANTIDAD-'].update('')
            window['-MEDIDA-'].update('')
            window['-PNOMINAL-'].update('')
            window['-STOCK-'].update('')

    # Binn Window events
    if window == bitacorasWindow:
        if event == '-SERVICES-':
            id_servicioFecha = values['-SERVICES-'].split(":")[0]
            mycursor.execute("SELECT fecha FROM servicios WHERE id_servicio=" + id_servicioFecha)
            window['-FECHABSOL-'].update(str(mycursor.fetchone()[0]))

        if event == 'fechasol':
            window['-FECHABSOL-'].update(formatDate(sg.popup_get_date()))
        if event == 'fechafin':
            window['-FECHABFIN-'].update(formatDate(sg.popup_get_date()))

        if event == 'guardarbinn':
            listedData = list(values.values())
            listedData.pop(0)
            # ['4: Formateo Ricardo', '0', '4', '2021-12-05', '2021-12-06', '1', '2', '3']
            listedData[0], listedData[1], listedData[2], listedData[3], listedData[4], listedData[5], listedData[6], listedData[7] = listedData[1], listedData[5], listedData[6], listedData[7], listedData[2], listedData[3], listedData[4], listedData[0]
            # [0, 1, '2', '3', 4, 5, 6
            for i in range(0, len(listedData)):
                if not listedData[i]:
                    sg.popup_error('ERROR: Ingrese valores en las casillas')
                    break
                elif listedData[i] and i == len(listedData) - 1:
                    temp_h = bitacoras_h[1:9]
                    print(temp_h)
                    mycursor.execute("INSERT INTO bitacoras" + parenth(temp_h, "") + "VALUES" + parenth(listedData, "'"))
                    myConnection.commit()
                    bitacoras, bitacoras_h = recoverItems('bitacoras')
                    window['-BINNTABLE-'].update(values=bitacoras)


            # listedData = list(values.values())
            # newThing(listedData[1:8], bitacoras, bitacoras_h)
            # window['-BINNTABLE-'].update(values=bitacoras)
        if event == 'deletebinn':
            delRows = values['-BINNTABLE-']
            if delRows:
                for index in sorted(delRows, reverse=True):
                    mycursor.execute("DELETE FROM bitacoras WHERE id_bitacora=" + bitacoras[index][0])
                    myConnection.commit()
                    bitacoras, bitacoras_h = recoverItems('bitacoras')
                    window['-BINNTABLE-'].update(values=bitacoras)
            else:
                print("Nothing selected")
        if event == 'emptybinn':
            window['-PROBLEM-'].update('')
            window['-DESCR-'].update('')
            window['-SOL-'].update('')
            window['-CAUSE-'].update('')
            window['-STATUS-'].update('')
            window['-FECHABSOL-'].update('')
            window['-FECHABFIN-'].update('')


    # Clients Window events
    if window == clientesWindow:
        if event == 'guardarcli':
            listedData = list(values.values())
            listedData.pop(0)
            for i in range(0, len(listedData)):
                if not listedData[i]:
                    sg.popup_error('ERROR: Ingrese valores en las casillas')
                    break
                elif listedData[i] and i == len(listedData) - 1:
                    temp_h = clientes_h[1:7]
                    print(temp_h)
                    mycursor.execute("INSERT INTO clientes" + parenth(temp_h, "") + "VALUES" + parenth(listedData, "'"))
                    myConnection.commit()
                    clientes, clientes_h = recoverItems('clientes')
                    window['-CLIENTTABLE-'].update(values=clientes)

        if event == 'deletecli':
            delRows = values['-CLIENTTABLE-']
            if delRows:
                for index in sorted(delRows, reverse=True):
                    mycursor.execute("DELETE FROM clientes WHERE id_cliente=" + clientes[index][0])
                    myConnection.commit()
                    clientes, clientes_h = recoverItems('clientes')
                    window['-CLIENTTABLE-'].update(values=clientes)
            else:
                print("Nothing selected")
        if event == 'emptycli':
            window['-DNI-'].update('')
            window['-FNAME-'].update('')
            window['-LNAME-'].update('')
            window['-EMAIL-'].update('')
            window['-PHONE-'].update('')
            window['-ADDR-'].update('')

# Closing
window.close()