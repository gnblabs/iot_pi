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


class MattressHeatMap:

    def __init__(self):
        self.serverURLNew = "https://iot.meidisheet.com/deviceLog"
        self.apiKey = "4dDDrkcqdv785ZdroOPD33c9XiJUsZ1taPqcEgAl"
        self.cpuserial = "0000000000000000"
        # GPIO.setwarnings(False)
        # GPIO.setmode(GPIO.BCM)
        self.LEDA = 24
        # GPIO.setup(self.LEDA, GPIO.OUT)    
        self.COLS = 24
        self.ROWS = 48
        self.Values = np.zeros((self.ROWS, self.COLS))
        self.RPosture = 0
        self.RPresence = 0
        self.CPX = 1
        self.CPY = 1
        self.ErrorCounter = 0
        self.ser = None
        print('sheet initialized')

    def prepareBed(self):
        self.ser = serial.Serial(
        port='/dev/ttyAMA0',
        baudrate=115200,
        timeout=3.0)
        time.sleep(1)
        self.StartReceiving()
        return True

    def StartReceiving(self):
        data = "S"
        self.ser.write(data.encode())
        print("Started")

    def StopReceiving(self):
        data = "X"
        self.ser.write(data.encode())
        print("Stoped")

    def internet_on(self):
        try:
            response = urllib2.urlopen('http://www.google.com', timeout=1)
            return True
        except urllib2.URLError as err:
            pass
        return False

    def listenForInternet(self):
        Internet_Status = self.internet_on()
        while not Internet_Status:
            # GPIO.output(LEDA, GPIO.HIGH)
            Internet_Status = self.internet_on()
            time.sleep(1)
        print('internet is available')
        return True

    def getserial(self):
        # Extract serial from cpuinfo file
        self.cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    self.cpuserial = line[10:26]
            f.close()
        except:
            self.cpuserial = "ERROR000000000"
        print('cpu serial '+self.cpuserial)
        return self.cpuserial

    def UploadPressureMap(self, PressureMap, RecognizedPosture, RecognizedPresence, MaxPressure, PressureCenterX, PressureCenterY):
        print("Posting to new Server ",self.serverURLNew)
        data = json.dumps({
                    'hardwareId': self.cpuserial,
                    'PressureMap': PressureMap,
                    'RecognizedPosture': RecognizedPosture,
                    'RecognizedPresence': RecognizedPresence,
                    'MaxPressure': MaxPressure,
                    'PressureCenterX': PressureCenterX,
                    'PressureCenterY': PressureCenterY
                })
        try:
            responseUloadPM = requests.request(
                'POST',
                self.serverURLNew,
                data= data,
                headers={
                    'content-type': 'application/json',
                    'x-api-key': self.apiKey
                }
            )
            print("data posted successfully!!! with status code {}".format(responseUloadPM.status_code))
        except requests.exceptions.ConnectionError as e:
            print('Connection refuse error in request at new server', e)
        return data

    def ReceiveRow(self, i):
        x = 0
        while x < self.ROWS:  # ROWS=48
            HighByte = self.ser.read()
            LowByte = self.ser.read()
            high = int.from_bytes(HighByte, 'big')
            # print(high)
            low = int.from_bytes(LowByte, 'big')
            # print(low)
            val = 4096 - ((low << 8) + high)
            if val < 0:
                print(val)

            self.Values[x][i] = val
            x += 1
        xbyte = self.ser.read().decode('utf-8')
        if xbyte != "\n":
            print('Communication Error')
    
    def ReceiveMap(self):
        y = 0
        while y < self.COLS:  # COLS=24
            xbyte = self.ser.read().decode('utf-8')
            if xbyte == 'M':
                # print(xbyte)
                xbyte = self.ser.read()
                xint = int.from_bytes(xbyte, 'big')
                # print(xint)
                if xint == self.ROWS:  # ROWS=48
                    xbyte = self.ser.read()
                    xint = int.from_bytes(xbyte, 'big')
                    # print(xint)
                    self.ReceiveRow(xint)
            y += 1

    def posture(self, Valuesx):
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

    def MaximumPressure(self, Valuesx):
        Max = 0
        for i in range(0, 47):
            for j in range(0, 23):
                if int(Valuesx[i][j]) > Max:
                    Max = int(Valuesx[i][j])
        return Max

    def CenterofPressureX(self, Valuesx):
        Mass = 0
        Mx = 0
        for i in range(0, 47):
            for j in range(0, 23):
                Mx += j*int(Valuesx[i][j])
                Mass += int(Valuesx[i][j])
        CenterX = int(Mx/Mass)
        return CenterX

    def CenterofPressureY(self, Valuesx):
        Mass = 0
        My = 0
        for i in range(0, 47):
            for j in range(0, 23):
                My += i*int(Valuesx[i][j])
                Mass += int(Valuesx[i][j])
        CenterY = int(My/Mass)
        return CenterY

    def listenForBedData(self):
        isSentData = False
        print('listening for data....')
        time.sleep(1)
        while self.ser.in_waiting > 0 and isSentData == False:
            xbyte = self.ser.read().decode('utf-8', errors='ignore')

            if xbyte == 'H':
                # print(xbyte)
                xbyte = self.ser.read()
                # print(xbyte)
                xbyte = self.ser.read().decode('utf-8', errors='ignore')
                self.ReceiveMap()
                ReceivedProperly = True
            else:
                print('Communication Error Could not receive H')
                print('ended at', datetime.now().strftime('%H:%M:%S'))
                ReceivedProperly = False
                self.StopReceiving()
                # sleep1seconds()
                # StartReceiving()

            if ReceivedProperly:
                # print(Values)
                print('Got some data, processing to post....')
                bValues = self.Values.tolist()
                # print(json.dumps(bValues))
                pm = json.dumps(bValues)
                self.StopReceiving()
                RPosture = self.posture(self.Values)
                print(self.Values)
                print('The posture is:')
                print(RPosture)
                if RPosture != 0:
                    RPresence = 1
                else:
                    RPresence = 0
                print('The maximum pressure is:')
                maxp = self.MaximumPressure(self.Values)
                print(maxp)
                print('The center of pressure in X is:')
                CPX = self.CenterofPressureX(self.Values)
                print(CPX)
                print('The center of pressure in Y is:')
                CPY = self.CenterofPressureY(self.Values)
                print(CPY)

                self.UploadPressureMap(pm, RPosture, RPresence, maxp, CPX, CPY)
                # sleepForSeconds(3)
                print('ended at', datetime.now().strftime('%H:%M:%S'))
                # StartReceiving()
                isSentData = True
        return True
            