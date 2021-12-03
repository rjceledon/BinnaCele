"""
Desarrollado por: Ing. Ricardo Celedon
Maracaibo, Venezuela, 12-3-2021
ricardocldn248@outlook.com
"""

import PySimpleGUI as sg # GUI Framework
import os # To get current working directory
import re # Regular expressions to filter filenames
import pickle # Module for saving data in binary streams
from datetime import datetime, timedelta # datetime to get curent date, timedelta to substract days from a date

sg.theme('Reddit') # SystemDefaultForReal

#VARIABLES
version = "0.4a" # Version number
todayDay = datetime.today().strftime('%Y-%m-%d') # Starting variable for today date match

# GUI variables

# Database headers
invItems_h = ["id_rubro", "rubro", "cantidad", "medida", "precio_nominal", "stock"]
services_h = ["id_servicio", "servicio", "departamento", "precio", "costo", "tiempo", "fecha"]
bitacoras_h = ["id_registro", "problema", "descripcion", "solucion", "causa", "sistemas", "estado", "fecha"]
clients_h = ["id_cliente", "dni", "nombre", "apellido", "correo", "telefono", "direccion"]

# Database data
companyName = ''
invItems = []
services = []
bitacoras = []
clients = []

dbFileName = ''
dbFilePath = ''

def loadFile(fileName):
    with open(fileName, 'rb') as filehandle:
        databaseFile = pickle.load(filehandle)
        return databaseFile

def saveFile(filename, filepath): # Filename, Path
    with open(filepath + '/' + filename, 'wb') as filehandle:
        # store the data as binary data stream
        dataBaseFile = [companyName, invItems, services, bitacoras, clients]
        pickle.dump(dataBaseFile, filehandle)

# Starting Load database

invalid_file = True # Flag for invalid file / Non existent

match sg.popup_yes_no('Desea abrir una compañia existente?\nOprima "No" para crear nueva'):
    case 'Yes': # Get popup result
        while not dbFilePath or invalid_file: # While dbFilePath is Null and invalid_file flag is True
            dbFilePath = sg.popup_get_file('Cargar archivo de compañia:', file_types=(("BinnaCele Data File", "*.bdata"), ("All file types", "*.*")))
            if dbFilePath == None: # If Cancel or close window, exit program
                exit(0)
            else:
                try: # Exceptions
                    dbFileName = dbFilePath.split('/')[-1]
                    dbFilePath = dbFilePath.replace('/' + dbFileName, '')
                    companyName, invItems, services, bitacoras, clients = loadFile(dbFilePath + '/' + dbFileName)
                    invalid_file = False
                except FileNotFoundError:
                    invalid_file = True
                    sg.popup('ERROR: El archivo no existe, por favor elija un archivo valido.')
                except PermissionError:
                    invalid_file = True
                    sg.popup('ERROR: No se puede abrir la ruta de archivo.')
                except OSError:
                    invalid_file = True
                    sg.popup('ERROR: No se puede abrir la ruta de archivo.')
                except pickle.UnpicklingError:
                    invalid_file = True
                    sg.popup('ERROR: Archivo no es valido.')

    case 'No':
        while not companyName: # While name is empty
            companyName = sg.popup_get_text('Ingrese el nombre de su compañia')
            match companyName:
                case None: # If Cancel or close window: exit program
                    exit(0)
                case '':
                    sg.popup('ERROR: Por favor ingrese un nombre de compañia')
                case _:
                    break # If there is some name, break

        dbFileName = re.sub(r"[^a-zA-Z0-9]+", "", companyName.lower()) + '.bdata'  # re.sub removes all characters that are not a-z or 0-9

        dbFilePath = sg.popup_get_folder('Guardar en carpeta:')
        if not dbFilePath: # If empty
            cwd = os.getcwd() # Use current working directory
            dbFilePath = cwd
            sg.popup('Compañia guardada en:', cwd) # Alert user where it was saved
        saveFile(dbFileName, dbFilePath) # Save

    case None:
        exit(0)

# New Item: It creates an element list in the required list
def newThing(listData, data, header): # listData is for values, data is for Database data name, and header is for database_h headers
    tempArray = ["{:04}".format(len(data)+1)] # Adding first element as 0001 identifier base on list position
    for column in range(1, len(header)):
        tempArray.append(listData[column-1]) # Appending passed data to list variable
    data.append(tempArray) # Adds temporal array to required data source list

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
    for fila in range(0,len(services)):
        if(services[fila][services_h.index("fecha")] >= date_s and services[fila][services_h.index("fecha")] <= date_f): # Iterate and adds only those values who are inside the required date range
            acum_precio += services[fila][services_h.index("precio")] # Add all prices and costs
            acum_costo += services[fila][services_h.index("costo")]
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
    formLayout = [[sg.Frame('Servicio', [[sg.Input(size=[25,1], key='-SERVICE-')]]), sg.Frame('Departamento', [[sg.InputCombo(("Telefonia", "Electrodomesticos", "Informatica", "Ciberseguridad"), default_value='Telefonia', key='-DPTO-')]]), sg.Frame('Precio ($)', [[sg.Input(size=[5,1], key='-PRICE-')]]), sg.Frame('Costo ($)', [[sg.Input(size=[5,1], key='-COST-')]])],
                  [sg.Frame('Tiempo', [[sg.Input(size=[10,1], key='-TIME-')]]), sg.Frame('Fecha', [[sg.Input(key='-FECHA-', disabled=True, size=[15,1]), sg.Button('Escoger fecha', key='fecha')]])]]


    layout = [[sg.Frame('Todos:', [[sg.Table(list(services), list(services_h), key='-SERVICESTABLE-', auto_size_columns=False,)]])],# Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20,20])],
              [sg.Frame('Registro nuevo Servicio:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardar'),sg.Button('Vaciar Campos', key='empty'),sg.Button('Borrar', key='delete')],
              [sg.Button('Salir', pad=[[630, 0], [0, 0]])]]

    return sg.Window('Servicios', layout, finalize=True, modal=True, element_justification='c')

def makeInvWindow():
    # "id_rubro", "rubro", "cantidad", "medida", "precio_nominal", "stock"
    formLayout = [[sg.Frame('Rubro', [[sg.Input(size=[25,1], key='-RUBRO-')]]), sg.Frame('Cantidad', [[sg.Input(size=[5,1], key='-CANTIDAD-')]]), sg.Frame('Medida', [[sg.Input(size=[8,1], key='-MEDIDA-')]])],
                  [sg.Frame('Precio Nominal ($)', [[sg.Input(size=[8,1], key='-PNOMINAL-')]]), sg.Frame('Stock', [[sg.Input(size=[10,1], key='-STOCK-')]])]]


    layout = [[sg.Frame('Existencias:', [[sg.Table(list(invItems), list(invItems_h), key='-INVTABLE-', auto_size_columns=False)]])], # Setting auto_size_columns false avoids error if opening with empty tables
              [sg.HorizontalSeparator(pad=[20,20])],
              [sg.Frame('Registro nuevo Item:', formLayout, element_justification='c')],
              [sg.Button('Guardar', key='guardarinv'),sg.Button('Vaciar Campos', key='emptyinv'),sg.Button('Borrar', key='deleteinv')],
              [sg.Button('Salir', pad=[[550, 0], [0, 0]])]]

    return sg.Window('Inventario', layout, modal=True, finalize=True, element_justification='c')

def makeBitacorasWindow():
    formLayout = [[sg.Frame('Problema', [[sg.Input(size=[20, 1], key='-PROBLEM-')]]), sg.Frame('Sistemas Afectados', [[sg.Input(size=[10, 1], key='-SYSTEMS-')]]),
                   sg.Frame('Estado', [[sg.Input(size=[10, 1], key='-STATUS-')]]),
                   sg.Frame('Fecha', [[sg.Input(key='-FECHAB-', disabled=True, size=[15,1]), sg.Button('Escoger fecha', key='fecha')]])],
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
                        [[sg.Table(list(clients), list(clients_h), key='-CLIENTTABLE-', auto_size_columns=False)]])],
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
    # print(event, values)
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
            saveFile(dbFileName, dbFilePath)
            balanceWindow.close()
            menuWindow.un_hide()
    if window == servicesWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            saveFile(dbFileName, dbFilePath)
            servicesWindow.close()
            menuWindow.un_hide()
    if window == invWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            saveFile(dbFileName, dbFilePath)
            invWindow.close()
            menuWindow.un_hide()
    if window == bitacorasWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            saveFile(dbFileName, dbFilePath)
            bitacorasWindow.close()
            menuWindow.un_hide()
    if window == clientesWindow:
        if event in (sg.WIN_CLOSED, 'Salir'):
            saveFile(dbFileName, dbFilePath)
            clientesWindow.close()
            menuWindow.un_hide()

    # Main GUI version

    # Balance Window events
    if window == balanceWindow:
        if event == 'diario':
            todayDay = datetime.today().strftime('%Y-%m-%d') # Getting current date with format YYYY-MM-DD
            # yesterdayDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
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

    # Services Window events
    if window == servicesWindow:
        if event == 'fecha':
            window['-FECHA-'].update(formatDate(sg.popup_get_date()))
        if event == 'guardar':
            listedData = list(values.values())


            try:
                listedData[3], listedData[4] = int(listedData[3]), int(listedData[4])
                newThing(listedData[1:7], services, services_h)
                window['-SERVICESTABLE-'].update(values=services)
            except ValueError:
                sg.popup('ERROR: Ingrese numeros en costo o precio')

            # listedData[3], listedData[4] = int(listedData[3]), int(listedData[4])
            # # print(listedData[1:7])
            # newThing(listedData[1:7], services, services_h)
            # window['-SERVICESTABLE-'].update(values=services)
        if event == 'delete':
            delRows = values['-SERVICESTABLE-'] # Rows to be deleted selected by the user and returned by the event
            if delRows: # If not empty
                for index in sorted(delRows, reverse=True):
                    print(index)
                    del services[index]
            else:
                print("Nothing selected")
            window['-SERVICESTABLE-'].update(values=services)
        if event == 'empty':
            window['-SERVICE-'].update('')
            window['-PRICE-'].update('')
            window['-COST-'].update('')
            window['-FECHA-'].update('')
            window['-TIME-'].update('')

    # Inv Window events
    if window == invWindow:
        if event == 'guardarinv':

            try:
                listedData = list(values.values())
                listedData[2], listedData[4], listedData[5] = int(listedData[2]), int(listedData[4]), int(listedData[5])
                newThing(listedData[1:6], invItems, invItems_h)
                window['-INVTABLE-'].update(values=invItems)
            except ValueError:
                sg.popup('ERROR: Ingrese numeros en precio nominal')

            # listedData = list(values.values())
            # newThing(listedData[1:6], invItems, invItems_h)
            # window['-INVTABLE-'].update(values=invItems)
        if event == 'deleteinv':
            delRows = values['-INVTABLE-']
            if delRows:
                for index in sorted(delRows, reverse=True):
                    print(index)
                    del invItems[index]
            else:
                print("Nothing selected")
            window['-INVTABLE-'].update(values=invItems)
        if event == 'emptyinv':
            window['-RUBRO-'].update('')
            window['-CANTIDAD-'].update('')
            window['-MEDIDA-'].update('')
            window['-PNOMINAL-'].update('')
            window['-STOCK-'].update('')

    # Binn Window events
    if window == bitacorasWindow:
        if event == 'fecha':
            window['-FECHAB-'].update(formatDate(sg.popup_get_date()))
        if event == 'guardarbinn':
            listedData = list(values.values())
            newThing(listedData[1:8], bitacoras, bitacoras_h)
            window['-BINNTABLE-'].update(values=bitacoras)
        if event == 'deletebinn':
            delRows = values['-BINNTABLE-']
            if delRows:
                for index in sorted(delRows, reverse=True):
                    print(index)
                    del bitacoras[index]
            else:
                print("Nothing selected")
            window['-BINNTABLE-'].update(values=bitacoras)
        if event == 'emptybinn':
            window['-PROBLEM-'].update('')
            window['-DESCR-'].update('')
            window['-SOL-'].update('')
            window['-CAUSE-'].update('')
            window['-SYSTEMS-'].update('')
            window['-STATUS-'].update('')
            window['-FECHAB-'].update('')

    # Clients Window events
    if window == clientesWindow:
        if event == 'guardarcli':

            try:
                listedData = list(values.values())
                # print(listedData)
                listedData[1] = int(listedData[1])
                listedData = list(values.values())
                newThing(listedData[1:7], clients, clients_h)
                window['-CLIENTTABLE-'].update(values=clients)
            except ValueError:
                sg.popup('ERROR: Ingrese cedula en numeros sin simbolos')

            # listedData = list(values.values())
            # newThing(listedData[1:7], clients, clients_h)
            # window['-CLIENTTABLE-'].update(values=clients)
        if event == 'deletecli':
            delRows = values['-CLIENTTABLE-']
            if delRows:
                for index in sorted(delRows, reverse=True):
                    print(index)
                    del clients[index]
            else:
                print("Nothing selected")
            # "id_cliente", "dni", "nombre", "apellido", "correo", "telefono", "direccion"
            window['-CLIENTTABLE-'].update(values=clients)
        if event == 'emptycli':
            window['-DNI-'].update('')
            window['-FNAME-'].update('')
            window['-LNAME-'].update('')
            window['-EMAIL-'].update('')
            window['-PHONE-'].update('')
            window['-ADDR-'].update('')

# Closing
saveFile(dbFileName, dbFilePath)
window.close()
