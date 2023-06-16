import time
import numpy as np
import serial
from datetime import datetime
import csv
import os
import requests
import json
import urllib.request as urllib2
import RPi.GPIO as GPIO

################################
email = "hardware@meidisheet.com"
password = "MHq6LvhWj6FbMwqK"
#serverURL = "http://3.19.148.230:3000" --Bilal
#serverURL = "http://52.15.139.169/api"
#serverURL = "http://136.37.144.209/api"
#serverURL = "http://64.227.29.161:3000"
#serverURL = "http://136.37.144.209:3000"
#serverURL = "http://136.33.195.113:3000"
#serverURL = "http://13.59.205.69/api"
serverURL = "http://167.172.228.39:3001"
# serverURLNew = "https://nlq1f26wwa.execute-api.us-east-1.amazonaws.com/beta/deviceLog"
serverURLNew = "https://iotdev.meidisheet.com/deviceLog"
cpuSerial = "0000000000000000"
################################


def getserial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"

  return cpuserial

cpuSerial = getserial()

def RequestAccessToken():
    try:
        responsetoken = requests.request(
            'POST',
            serverURL + '/auth/login',
            data=json.dumps({'email': email, 'password': password}),
            headers={'content-type': 'application/json'}
        )
        return json.loads(responsetoken.text)['token']
    except requests.exceptions:
        print('Cannot receive Access Token')
        return 'Error'


def UploadPressureMap(PressureMap, RecognizedPosture, RecognizedPresence, MaxPressure, PressureCenterX, PressureCenterY):
    
    print("Posting to new Server ",serverURLNew)
    try:
        responseUloadPM = requests.request(
            'POST',
            serverURLNew,
            data=json.dumps({
                'hardwareId': cpuSerial,
                'PressureMap': PressureMap,
                'RecognizedPosture': RecognizedPosture,
                'RecognizedPresence': RecognizedPresence,
                'MaxPressure': MaxPressure,
                'PressureCenterX': PressureCenterX,
                'PressureCenterY': PressureCenterY
            }),
            headers={
                'content-type': 'application/json',
                'x-api-key': 'k34rJRlvoJ2g31TzUeGh1alLdiQsHcMG4CFGaYkM'
            }
        )
    except requests.exceptions.ConnectionError as e:
        print('Connection refuse error in request at new server', e)
    
    # print("Posting to Old Server ",serverURL)
    # try:
    #     responseUloadPM = requests.request(
    #         'POST',
    #         serverURL + '/pressureMap',
    #         data=json.dumps({
    #             'hardwareId': cpuSerial,
    #             'PressureMap': PressureMap,
    #             'RecognizedPosture': RecognizedPosture,
    #             'RecognizedPresence': RecognizedPresence,
    #             'MaxPressure': MaxPressure,
    #             'PressureCenterX': PressureCenterX,
    #             'PressureCenterY': PressureCenterY
    #         }),
    #         headers={
    #             'content-type': 'application/json'
    #         }
    #     )
    # except requests.exceptions.ConnectionError:
    #     print('Connection refuse error in request at old server')
        
    return


def StartReceiving():
    data = "S"
    ser.write(data.encode())
    print("Started")


def StopReceiving():
    data = "X"
    ser.write(data.encode())
    print("Stoped")

#################################


# set up of LED output pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
LEDA = 24
GPIO.setup(LEDA, GPIO.OUT)

print('started at', datetime.now().strftime('%H:%M:%S'))

# Function to check internet connection, returns True if internet is connected otherwise it returns False.


def internet_on():
    try:
        response = urllib2.urlopen('http://www.google.com', timeout=1)
        return True
    except urllib2.URLError as err:
        pass
    return False


# This will check the internet connection status
Internet_Status = internet_on()

# Loop to indicate the network disconnection and wait 1 second to check if the network is connected

# Led indicator is turned on in order to notify the problem.
while not Internet_Status:
    GPIO.output(LEDA, GPIO.HIGH)
    Internet_Status = internet_on()
    time.sleep(1)

GPIO.output(LEDA, GPIO.LOW)

#################################
# MATRIX FOR THE PRESSURE DATA
COLS = 24
ROWS = 48

Values = np.zeros((ROWS, COLS))

ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=115200,
    timeout=3.0)
time.sleep(1)
StartReceiving()


def sleep1minute():
    time.sleep(60)
    ser.flushInput()
    ser.flushOutput()


def sleep15seconds():
    time.sleep(15)
    ser.flushInput()
    ser.flushOutput()


def sleep5seconds():
    time.sleep(5)
    ser.flushInput()
    ser.flushOutput()


def sleep1seconds():
    time.sleep(1)
    ser.flushInput()
    ser.flushOutput()


def sleepForSeconds(seconds):
    time.sleep(seconds)
    ser.flushInput()
    ser.flushOutput()


def ReceiveRow(i):
    x = 0
    while x < ROWS:  # ROWS=48
        HighByte = ser.read()
        LowByte = ser.read()
        high = int.from_bytes(HighByte, 'big')
        # print(high)
        low = int.from_bytes(LowByte, 'big')
        # print(low)
        val = 4096 - ((low << 8) + high)
        if val < 0:
            print(val)

        Values[x][i] = val
        x += 1
    xbyte = ser.read().decode('utf-8')
    if xbyte != "\n":
        print('Communication Error')


def ReceiveMap():
    y = 0
    while y < COLS:  # COLS=24
        xbyte = ser.read().decode('utf-8')
        if xbyte == 'M':
            # print(xbyte)
            xbyte = ser.read()
            xint = int.from_bytes(xbyte, 'big')
            # print(xint)
            if xint == ROWS:  # ROWS=48
                xbyte = ser.read()
                xint = int.from_bytes(xbyte, 'big')
                # print(xint)
                ReceiveRow(xint)
        y += 1


def posture(Valuesx):
    sensoresActivadosTotales = 0
    sumatorioPresionesTotal = 0
    presionMaximaTotal = 0
    sensoresActivadosPorQuadrante = np.zeros((7, 7))
    sumatorioPresionesPorQuadrante = np.zeros((7, 7))
    sensoresActivadosPorColumna = np.zeros((23))
    sensoresActivadosPorFila = np.zeros((48))
    sumatorioPresionesPorColumna = 0
    sumatorioPresionesPorFila = 0
    maximoPorQuadrante = np.zeros((7, 7))
    mediaPorQuadrante = np.zeros((7, 7))
    quadranteX = 0
    quadranteY = 0

    for i in range(0, 47):
        for j in range(0, 23):

            # Values[i][j]
            quadranteX = int(round(i / 8))
            quadranteY = int(round(j / 4))
            if quadranteY >= 6:
                quadranteY = 5
            if quadranteX > 6:
                quadranteX = 5
            # Valores por quadrante
            sumatorioPresionesPorQuadrante[quadranteX][quadranteY] += int(
                Valuesx[i][j])
            if Valuesx[i][j] > 0:
                sensoresActivadosPorQuadrante[quadranteX][quadranteY] += 1
            if Valuesx[i][j] > maximoPorQuadrante[quadranteX][quadranteY]:
                maximoPorQuadrante[quadranteX][quadranteY] = int(Valuesx[i][j])

            # Valores globales

            sumatorioPresionesTotal += int(Valuesx[i][j])

            if Valuesx[i][j] > 0:
                sensoresActivadosTotales += 1
            if Valuesx[i][j] > presionMaximaTotal:
                presionMaximaTotal = int(Valuesx[i][j])

    for i in range(0, 6):
        for j in range(0, 6):

            if sensoresActivadosPorQuadrante[i][j] == 0:
                mediaPorQuadrante[i][j] = 0

            else:
                mediaPorQuadrante[i][j] = sumatorioPresionesPorQuadrante[i][j] / \
                    sensoresActivadosPorQuadrante[i][j]

    if sumatorioPresionesTotal < 100000:
        return 0

    else:

        if sumatorioPresionesTotal < 250000:
            return 5

        else:

            switches = np.zeros((6))

            for iterator in range(0, 6):
                switches[iterator] = mediaPorQuadrante[5][iterator] > 600

            cambios = 0

            for iterator in range(0, 6):
                if switches[iterator] != switches[iterator-1]:
                    cambios = cambios+1

            if cambios == 0:
                for iterator in range(0, 6):
                    switches[iterator] = mediaPorQuadrante[4][iterator] > 600

                cambios = 0

                for iterator in range(0, 6):

                    if switches[iterator] != switches[iterator-1]:
                        cambios = cambios+1

                if cambios == 0:
                    return 5

                else:
                    return 2

            # Sabemos que esta tumbado
            else:

                # Piernas Juntas
                if (((switches[0] == False)and(cambios <= 2))or((switches[0] == True)and(cambios == 1))):
                    derecha = sensoresActivadosPorQuadrante[3][0] + sensoresActivadosPorQuadrante[3][1]+sensoresActivadosPorQuadrante[3][2] + \
                        sensoresActivadosPorQuadrante[4][0] + \
                        sensoresActivadosPorQuadrante[4][1] + \
                        sensoresActivadosPorQuadrante[4][2]
                    izquierda = sensoresActivadosPorQuadrante[3][3] + sensoresActivadosPorQuadrante[3][4]+sensoresActivadosPorQuadrante[3][5] + \
                        sensoresActivadosPorQuadrante[4][3] + \
                        sensoresActivadosPorQuadrante[4][4] + \
                        sensoresActivadosPorQuadrante[4][5]

                    if izquierda >= derecha:
                        return 3

                    else:
                        return 4
                else:
                    primera = sensoresActivadosPorQuadrante[0][0] + sensoresActivadosPorQuadrante[0][1] + sensoresActivadosPorQuadrante[0][2] + \
                        sensoresActivadosPorQuadrante[0][3] + \
                        sensoresActivadosPorQuadrante[0][4] + \
                        sensoresActivadosPorQuadrante[0][5]
                    segunda = sensoresActivadosPorQuadrante[1][0] + sensoresActivadosPorQuadrante[1][1] + sensoresActivadosPorQuadrante[1][2] + \
                        sensoresActivadosPorQuadrante[1][3] + \
                        sensoresActivadosPorQuadrante[1][4] + \
                        sensoresActivadosPorQuadrante[1][5]

                    if segunda >= primera:
                        return 1
                    else:
                        return 2


def MaximumPressure(Valuesx):
    Max = 0
    for i in range(0, 47):
        for j in range(0, 23):
            if int(Valuesx[i][j]) > Max:
                Max = int(Valuesx[i][j])
    return Max


def CenterofPressureX(Valuesx):
    Mass = 0
    Mx = 0
    for i in range(0, 47):
        for j in range(0, 23):
            Mx += j*int(Valuesx[i][j])
            Mass += int(Valuesx[i][j])
    CenterX = int(Mx/Mass)
    return CenterX


def CenterofPressureY(Valuesx):
    Mass = 0
    My = 0
    for i in range(0, 47):
        for j in range(0, 23):
            My += i*int(Valuesx[i][j])
            Mass += int(Valuesx[i][j])
    CenterY = int(My/Mass)
    return CenterY


RPosture = 0
RPresence = 0
CPX = 1
CPY = 1
ErrorCounter = 0

actualtoken = RequestAccessToken()

# while True:
while ser.in_waiting > 0:
    xbyte = ser.read().decode('utf-8', errors='ignore')

    if xbyte == 'H':
        # print(xbyte)
        xbyte = ser.read()
        # print(xbyte)
        xbyte = ser.read().decode('utf-8', errors='ignore')
        ReceiveMap()
        ReceivedProperly = True
    else:
        print('Communication Error Could not receive H')
        print('ended at', datetime.now().strftime('%H:%M:%S'))
        ReceivedProperly = False
        StopReceiving()
        # sleep1seconds()
        # StartReceiving()

    if ReceivedProperly:
        # print(Values)
        bValues = Values.tolist()
        # print(json.dumps(bValues))
        pm = json.dumps(bValues)
        StopReceiving()
        RPosture = posture(Values)
        print(Values)
        print('The posture is:')
        print(RPosture)
        if RPosture != 0:
            RPresence = 1
        else:
            RPresence = 0
        print('The maximum pressure is:')
        maxp = MaximumPressure(Values)
        print(maxp)
        print('The center of pressure in X is:')
        CPX = CenterofPressureX(Values)
        print(CPX)
        print('The center of pressure in Y is:')
        CPY = CenterofPressureY(Values)
        print(CPY)

        UploadPressureMap(pm, RPosture, RPresence, maxp, CPX, CPY)
        sleepForSeconds(3)
        print('ended at', datetime.now().strftime('%H:%M:%S'))
        # StartReceiving()
