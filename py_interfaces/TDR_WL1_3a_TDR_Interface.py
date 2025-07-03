from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from tkinter import *
import numpy as np
import string
import tkinter
import math
import random
import aioserial
import asyncio
import sys
import glob
import serial
import serial.tools.list_ports as ports
import time
import os
import datetime
import shutil


#revisions:
#TDR_WL1_3a:
# startup trace scaled to sampling rate
# saving of all tree trace added

#
#REMAININGS:
# loading of all tree traces should be added
# 3050 model sampling features are not included
# trace gray/yellow/red bugs
# single/multiple/trigger options not completed
#  manual pulse/gain models should have disabled buttons  


##scope = rm.open_resource(visa_address)
##scope.timeout = 10000 # ms
##scope.encoding = 'latin_1'
##scope.write_termination = None

if os.name=='nt':
    import pyvisa as visa # http://github.com/hgrecco/pyvisa
    from tkinter import filedialog
    from tkinter.filedialog import asksaveasfile
    from tkinter.filedialog import asksaveasfilename
    from tkinter import messagebox
    
    visa_address = 'USB0::0x1AB1::0x0588::DS1EB142204615::INSTR'
    rm = visa.ResourceManager()
    TARGETOS='WINDOWS' #PI WINDOWS
    import screeninfo
    tdrwd=os.getcwd()
else:
    TARGETOS='PI'        #PI WINDOWS
    if os.path.exists('/home/gd/Desktop'):
        tdrwd='/home/gd/Desktop'
    else:
        tdrwd='/home/pi/Desktop'
    fullsetuppath =os.path.join(tdrwd,'setup.txt')
    
print("working directory:",tdrwd)    
   
instrument='none'
samplingrate=10.0   #nanoseconds
refKP=-1
counterKP=0

MouseXfp=0
MouseXsp=0
firstmousepntx=-1

ViewRange=100.0
ViewStart=0
PVeloc05Metric=100
PulseWidths={0:'Pulse: 50ns',1:'Pulse:100ns',2:'Pulse:200ns',3:'Pulse:500ns',4:'Pulse: 1 us',5:'Pulse: 2 us',6:'Pulse: 5 us',7:'Pulse: 10us'}
PulseWidth=0
Gain=5
Marker1Pos=0.0
Marker2Pos=0.0

ActiveTrace=0
TraceEmpty=0
TraceDisabled=1
TraceAuto=2
TraceSngl=3
TraceMult=4
TraceWithTrig=5
#TraceSngl
Trace1Header={'state':TraceSngl, 'visible': 1, 'tracetype':TraceEmpty, 'sampling':10.0, 'range':4096, 'pulse':0 , 'gain':5 , 'trigger':0 , 'multiple':0 }
Trace2Header={'state':TraceEmpty, 'visible': 0, 'tracetype':TraceEmpty, 'sampling':10.0, 'range':4096, 'pulse':0 , 'gain':5 , 'trigger':0 , 'multiple':0}
Trace3Header={'state':TraceEmpty, 'visible': 0, 'tracetype':TraceEmpty, 'sampling':10.0, 'range':4096, 'pulse':0 , 'gain':5 , 'trigger':0 , 'multiple':0}

SignalLen=4096
Signal1Len=SignalLen
Signal1Xvals = np.zeros(Signal1Len)
Signal1Yvals = np.zeros(Signal1Len)

for i in range(Signal1Len):
    Signal1Xvals[i]=float(i)*0.000000010
    val=128
    if i==20 : val=250.0
    if i>20: val=128+(Signal1Yvals[i-1]-128)*0.9
    Signal1Yvals[i]=val
##for i in range(Signal1Len):
##    Signal1Xvals[i]=float(i)
##    Signal1Yvals[i]=118
    
Signal2Len=SignalLen
Signal2Xvals = np.zeros(Signal2Len)
Signal2Yvals = np.zeros(Signal2Len)
for i in range(Signal2Len):
    Signal2Xvals[i]=float(i)
    Signal2Yvals[i]=118
    
Signal3Len=SignalLen
Signal3Xvals = np.zeros(Signal3Len)
Signal3Yvals = np.zeros(Signal3Len)
for i in range(Signal3Len):
    Signal3Xvals[i]=float(i)
    Signal3Yvals[i]=138

SignalEvenXvals = np.zeros(SignalLen)
SignalEvenYvals = np.zeros(SignalLen)
SignalOddXvals = np.zeros(SignalLen)
SignalOddYvals = np.zeros(SignalLen)
##Marker1Xvals=np.zeros(2)
##Marker1Xvals[0],Marker1Xvals[1]=10.0,10.0
##Marker1Yvals=np.zeros(2)
##Marker1Yvals[0],Marker1Yvals[1]=0,255
##Marker2Xvals=np.zeros(2)
##Marker2Xvals[0],Marker2Xvals[1]=100.0,100.0
##Marker2Yvals=np.zeros(2)
##Marker2Yvals[0],Marker2Yvals[1]=0,255

resultlist = []
selectedComport=''
OnlineMode=0
deviceDescription="NO\nDEVICE*"
deviceDescription2="NO\nDEVICE*"
meters_time=0

if TARGETOS=='PI':

    def DetectConnectedDevices():
        check_serial_ports()

    def GetUsbList() : return os.popen("lsusb").read().strip().split("\n")
    def GetDevList() : return os.listdir("/dev")

##    def Changed(old, now):
##
##        add = []
##        rem = []
##        for this in now:
##            if not this in old:
##                add.append(this)
##        for this in old:
##          if not this in now:
##            rem.append(this)
##        return add, rem
    
    def check_serial_ports():
        global ser
        global resultlist
        global OnlineMode
        global selectedComport
      
        usbOld, devOld = GetUsbList(), GetDevList()
        print (usbOld,devOld)
  #initialize serial port
      #if len(resultlist)>0:
      #if '/dev/ttyACM0' in devOld:
    
        try:    
            selectedComport='/dev/ttyACM0'

            ser = serial.Serial(
                port=selectedComport,
                baudrate =115200 ,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=2)

            ser.reset_input_buffer()
            time.sleep(2)
            if (ser.is_open==True):
                print("\nAll right, serial port now open. Configuration:\n")        
                OnlineMode=2
                print('OnlineMode2 selected')

        except:
            if OnlineMode==0:
                print('OnlineMode0 selected')
                #disableButtons(-1)
                #destroy()
                #time.sleep(2)


if TARGETOS=='WINDOWS':
    def DetectConnectedDevices():
        global resultlist
        global selectedComport
        global ser
        global OnlineMode
        global instrument
        global samplingrate
        global deviceDescription
        global deviceDescription2
        
        #works with windows only
        ports = ['COM%s' % (i + 1) for i in range(256)]

        for port in ports:
          try:
              
              s = serial.Serial(port)
              s.close()
              if port!='COM5':
                  resultlist.append(port)
          except (OSError, serial.SerialException):
              pass
    
        print(resultlist)

        #first scan of serial ports
        for eachresult in resultlist:
            print(eachresult)
            ser = serial.Serial(eachresult,115200 ,timeout=2)
            ser.set_buffer_size(rx_size = 25600, tx_size = 25600)
            
            if (ser.is_open==True):
                ser.reset_input_buffer()
                ser.write( 'ver\n'.encode())
                Txtmsg=(ser.readline()).decode('utf8')
                if len(Txtmsg)>12 and Txtmsg[:13]=='TDR_with F411':
                    print(Txtmsg)
                    selectedComport=eachresult
                    instrument='F411'
                    samplingrate=10.417
                    deviceDescription="F411\n10.417ns"
                    OnlineMode=2
                    
                    ser.reset_input_buffer()
                    ser.write( 'sampling\n'.encode())
                    Txtmsg=(ser.readline()).decode('utf8')
                    print('samplingrate:',Txtmsg)
                    if Txtmsg[:7]=='5.208ns':
                        samplingrate=5.208  #nanoseconds
                        deviceDescription="F411\n5.208ns"

                    print(Txtmsg,samplingrate)
                    ser.close() #found a familiar device, close for now
                    break
                
                ser.close() #close and check next one
              
                
        # if not found a familier device try again
        if OnlineMode==0:
            print ("no familiar device found")
            for eachresult in resultlist:
                ser = serial.Serial(eachresult,115200 ,timeout=2)
                ser.set_buffer_size(rx_size = 25600, tx_size = 25600)
                print("serial port",eachresult)
                if (ser.is_open==True):
                    ser.reset_input_buffer()
                    selectedComport=eachresult
                    instrument='Unknown'
                    samplingrate=1166.666
                    deviceDescription="Unknown"
                    OnlineMode=2
                    
                    ser.close()
                    break
        
        if OnlineMode==2: #reopen again
            ser = serial.Serial(eachresult,115200 ,timeout=4)
            ser.set_buffer_size(rx_size = 25600, tx_size = 25600)
            if (ser.is_open==True):
                    if instrument=='Unknown':
                        instrument='Ultrasonic'
                        deviceDescription="Ultrasonic"
                    print("serial port is re-opened:",instrument)
                    
        if OnlineMode==0:
            print('no serial port device found')
              #disableButtons(-1)

        #check oscilloscope
        try:
            selectMenuFunction(4)
            disableButtons(-1)
            gui.update()
            initiateRIGOL()
     
            if deviceDescription=="NO\nDEVICE*":
                deviceDescription="RIGOL\nDS1102E"
            else:
                deviceDescription2=deviceDescription
                deviceDescription="RIGOL\nDS1102E\nW/TDR"
        except:
            pass
        selectMenuFunction(4)
        enableButtons(ActiveButton)
        gui.update()
        
    def check_serial_ports():
        global resultlist
        global selectedComport
        #works with windows only
        ports = ['COM%s' % (i + 1) for i in range(256)]

        for port in ports:
          try:
              s = serial.Serial(port)
              s.close()
              resultlist.append(port)
          except (OSError, serial.SerialException):
              pass
          
        print(resultlist)
        if len(resultlist)>0:
            print(resultlist[0])
            selectedComport=resultlist[0]
            SerialOpen()
            if len(resultlist)>1:
                print(resultlist[1])
        else:
            print('no serial port found')
              #disableButtons(-1)
            
    def SerialOpen():
        global ser
        global resultlist
        global OnlineMode
        global selectedComport
        global instrument
        global samplingrate
      
      #initialize serial port
        if len(resultlist)>0:
            ser = serial.Serial(resultlist[0],115200 ,timeout=8)
            ser.set_buffer_size(rx_size = 25600, tx_size = 25600)
            ser.reset_input_buffer()
            if (ser.is_open==True):
                print("\nAll right, serial port now open. Configuration:\n")
                OnlineMode=2
                print('OnlineMode2 selected')

                ser.reset_input_buffer()
                ser.write( 'ver\n'.encode())
                Txtmsg=(ser.readline()).decode('utf8')[:13]
                if Txtmsg=='TDR_with F411':
                    print(Txtmsg)
                    instrument='F411'
                    samplingrate=10.417
                    
                    ser.reset_input_buffer()
                    ser.write( 'sampling\n'.encode())
                    Txtmsg=(ser.readline()).decode('utf8')[:7]
                    print('samplingrate:',Txtmsg)
                    if Txtmsg[:7]=='5.208ns':
                        samplingrate=5.208  #nanoseconds
                        print(Txtmsg,samplingrate)
#----------------------------------------------------------------------------------------------
              
        if OnlineMode==0:
            disableButtons(-1)
      #time.sleep(2)

def UpdateDisplay():
    global Signal1Range
    global Signal2Range
    global Signal3Range
    global ViewRange
    global ViewStart
    global ActiveButton
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global trcBtns
    global CheckBoxsamplesVar

    if deviceDescription[:8]=="Ultrason":
        UpdateDisplay2()
        return
    ax.clear()
           
    ax.set_title('TDR DATA')
    ax.set_xlabel('METERS')
    ax.set_ylabel('RAW ADC DATA')
    
##    ax.set_xlim(float(TLeftVar.get()), float(TRightVar.get()))
##    ax.set_ylim(float(TBottomVar.get()), float(TTopVar.get()))

    ax.set_xlim( ViewStart , ViewStart+ViewRange)
    ax.set_ylim(0, 255)

    ax.grid( which='major', color='#666666', linestyle='-')
    ax.minorticks_on()
    ax.grid( which='minor', color='#666666', linestyle='-', alpha=0.4)
    
    PVeloc2=PVeloc05Metric/1000/1E-9
    print ('PVeloc05Metric:',PVeloc05Metric)
    print ('samplingrate:',samplingrate)
    print ('pveloc2:',PVeloc2)
    print('ilk sample:',Signal1Xvals[1]*PVeloc2)
    
    #if  Trace1Header['state']!=TraceEmpty and Trace1Header['state']!=TraceDisabled:
    #  trcBtns[0].cget('bg') != 'gray':
    if CheckBoxsamplesVar.get()==0:
        if  Trace1Header['visible']==1:
            line0,=ax.plot(Signal1Xvals*PVeloc2, Signal1Yvals, linestyle='solid' \
                                              ,color='black') # dotted, solid,

        if  Trace2Header['visible']==1:
            line1,=ax.plot(Signal2Xvals*PVeloc2, Signal2Yvals, linestyle='solid' \
                                              ,color='blue') # dotted, solid,
    
        if  Trace3Header['visible']==1:
            line2,=ax.plot(Signal3Xvals*PVeloc2, Signal3Yvals, linestyle='solid' \
                                                  ,color='red') # dotted, solid,
    else:
        if  Trace1Header['visible']==1:
            line0,=ax.plot(Signal1Xvals*PVeloc2, Signal1Yvals, '-k.' \
                                                 ,markevery = 1 ) # dotted, solid,

        if  Trace2Header['visible']==1:
            line1,=ax.plot(Signal2Xvals*PVeloc2, Signal2Yvals, '-b.' \
                                                 ,markevery = 1 ) # dotted, solid,
            
        if  Trace3Header['visible']==1:
            line2,=ax.plot(Signal3Xvals*PVeloc2, Signal3Yvals, '-r.' \
                                                 ,markevery = 1 ) # dotted, solid,

        #below is for the stereo uson detector
##            for i in range (len(Signal3Xvals)):
##                if i%2==0:
##                    SignalEvenXvals[i]=Signal3Xvals[i]
##                    SignalEvenYvals[i]=Signal3Yvals[i]
##                else:
##                    SignalEvenXvals[i]=Signal3Xvals[i-1]
##                    SignalEvenYvals[i]=Signal3Yvals[i-1]
##                    
##            for i in range (len(Signal3Xvals)):
##                if i%2==0:
##                    SignalOddXvals[i]=Signal3Xvals[i+1]
##                    SignalOddYvals[i]=Signal3Yvals[i+1]
##                else:
##                    SignalOddXvals[i]=Signal3Xvals[i]
##                    SignalOddYvals[i]=Signal3Yvals[i]                    

##            line3,=ax.plot(SignalEvenXvals*PVeloc2, SignalEvenYvals, '-m.' ,markevery = 1 ) # dotted, solid,
##            line4,=ax.plot(SignalOddXvals*PVeloc2, SignalOddYvals, '-g.' ,markevery = 1 ) # dotted, solid,
    plt.draw()
    fig.canvas.flush_events()
    updateMarkerPositions()

def UpdateDisplay2():
    global Signal1Range
    global Signal2Range
    global Signal3Range
    global ViewRange
    global ViewStart
    global ActiveButton
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global trcBtns
    global CheckBoxsamplesVar
  
    ax.clear()
           
    ax.set_title('ULTRASONIC DATA')
    ax.set_xlabel('TIME (microseconds)')
    ax.set_ylabel('RAW ADC DATA')
    
##    ax.set_xlim(float(TLeftVar.get()), float(TRightVar.get()))
##    ax.set_ylim(float(TBottomVar.get()), float(TTopVar.get()))

    ax.set_xlim( ViewStart , ViewStart+ViewRange)
    ax.set_ylim(0, 4096)

##    ax.grid( which='major', color='#666666', linestyle='-')
##    ax.minorticks_on()
##    ax.grid( which='minor', color='#666666', linestyle='-', alpha=0.4)
    
    #PVeloc2=PVeloc05Metric/1000/1E-9
    PVeloc2=1000000.0
    print ('PVeloc05Metric:',PVeloc05Metric)
    print ('samplingrate:',samplingrate)
    print ('pveloc2:',PVeloc2)
    print('ilk sample:',Signal1Xvals[1]*PVeloc2)
    
    #if  Trace1Header['state']!=TraceEmpty and Trace1Header['state']!=TraceDisabled:
    #  trcBtns[0].cget('bg') != 'gray':
    if CheckBoxsamplesVar.get()==0:
        if  Trace1Header['visible']==1:
            line0,=ax.plot(Signal1Xvals*PVeloc2, Signal1Yvals, linestyle='solid' \
                                              ,color='black') # dotted, solid,

        if  Trace2Header['visible']==1:
            line1,=ax.plot(Signal2Xvals*PVeloc2, Signal2Yvals, linestyle='solid' \
                                              ,color='blue') # dotted, solid,
    
        if  Trace3Header['visible']==1:
                line2,=ax.plot(Signal3Xvals*PVeloc2, Signal3Yvals, linestyle='solid' \
                                                  ,color='red') # dotted, solid,
    else:
        if  Trace1Header['visible']==1:
            line0,=ax.plot(Signal1Xvals*PVeloc2, Signal1Yvals, '-k.' \
                                                 ,markevery = 1 ) # dotted, solid,

        if  Trace2Header['visible']==1:
            line1,=ax.plot(Signal2Xvals*PVeloc2, Signal2Yvals, '-b.' \
                                                 ,markevery = 1 ) # dotted, solid,
            
        if  Trace3Header['visible']==1:
            line2,=ax.plot(Signal3Xvals*PVeloc2, Signal3Yvals, '-r.' \
                                                 ,markevery = 1 ) # dotted, solid,

            for i in range (len(Signal3Xvals)):
                if i%2==0:
                    SignalEvenXvals[i]=Signal3Xvals[i]
                    SignalEvenYvals[i]=Signal3Yvals[i]
                else:
                    SignalEvenXvals[i]=Signal3Xvals[i-1]
                    SignalEvenYvals[i]=Signal3Yvals[i-1]
                    
            for i in range (len(Signal3Xvals)):
                if i%2==0:
                    SignalOddXvals[i]=Signal3Xvals[i+1]
                    SignalOddYvals[i]=Signal3Yvals[i+1]
                else:
                    SignalOddXvals[i]=Signal3Xvals[i]
                    SignalOddYvals[i]=Signal3Yvals[i]                    

##            line3,=ax.plot(SignalEvenXvals*PVeloc2, SignalEvenYvals, '-m.' ,markevery = 1 ) # dotted, solid,
##            line4,=ax.plot(SignalOddXvals*PVeloc2, SignalOddYvals, '-g.' ,markevery = 1 ) # dotted, solid,
    plt.draw()
    fig.canvas.flush_events()
    updateMarkerPositions()

def update(score,limit):
    global timer
    global refKP
    global counterKP
    
    Txtmsg=ser.readline().decode('ascii')
    if len(Txtmsg)!=0:
        Txtmsg=Txtmsg[:-2]
        if Txtmsg.isnumeric():
            n=int(Txtmsg)
            if refKP==-1:
                refKP=n
                counterKP=0
            else:
                increment=n-refKP
                if increment<-64: increment+=128
                if increment>64 : increment-=128
                refKP=n
                counterKP-=increment
                if counterKP<0: counterKP=0
                if counterKP>10: counterKP=10
                print(counterKP)
        else:
            print(Txtmsg)
    timer = gui.after(50,update, score,limit)


def ACQFunction_F411(): #this is for TDR 19.2 MHz
    global OnlineMode
    global ser
    global LTDRPulse
    global LTDRGain
    global Trace1Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    global samplingrate

    if OnlineMode==0:
        return()
    
    try:            
        ser.reset_input_buffer()
        
        txt='ver\n'
        res= txt.encode()
        ser.write(res)
        Txtmsg=ser.readline()
        print('ver:',Txtmsg)
              
        txt='sampling\n'
        res= txt.encode()
        ser.write(res)
        Txtmsg=(ser.readline()).decode('utf8')[:7]
        print('sampling:',Txtmsg)
        if Txtmsg[:7]=='5.208ns':
            samplingrate=5.208  #nanoseconds
        if Txtmsg[:7]=='10.416ns':
            samplingrate=10.416  #nanoseconds

        txt='multi=2\n'
        res= txt.encode()
        ser.write(res)
        Txtmsg=ser.readline()
        print('multi:',Txtmsg)
        
        txt='capture\n'
        res= txt.encode()
        ser.write(res)
        Txtmsg=ser.readline()
        
        txt='read\n'
        res= txt.encode()
        ser.write(res)
        time.sleep(0.1)
        Txtmsg=ser.readline()                       #timeout veya \n gelene kadar bekliyor
        #splittedText=Txtmsg.split()

        splittedText=Txtmsg.split()
        
##        if ActiveTrace==0:
##                splittedText2=Txtmsg.split()
##                llen=len(splittedText2)
##                splittedText=[]
##                for i in range(llen-2):
##                    if i%2==0:
##                        splittedText.append(splittedText2[i])
##                    else:
##                        splittedText.append((splittedText2[i]+splittedText2[i+2])/2)
##                        
##        if ActiveTrace==1:
##                splittedText2=Txtmsg.split()
##                llen=len(splittedText2)
##                splittedText=[]
##                for i in range(llen-2):
##                    if i%2==1:
##                        splittedText.append(splittedText2[i])
##                    else:
##                        splittedText.append((splittedText2[i]+splittedText2[i])/2)
                        
        if ActiveTrace==0:
            Trace1Header['state']=TraceSngl
            Trace1Header['visible']=1
            Trace1Header['tracetype']=TraceSngl
            Trace1Header['sampling']=samplingrate
            Trace1Header['range']=4096
            Trace1Header['pulse']=0
            Trace1Header['gain']=0
            Trace1Header['trigger']=0
            Trace1Header['multiple']=0

            Signal1Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(1):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=float(splittedText[i])
##                        if 1:
##                        #if i%2==1:
##                            z=.5*float(splittedText[i-1])+.5*float(splittedText[i+1])
                        zi=i
                        Signal1Yvals[i]=z
                        Signal1Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal1Yvals[i]=Signal1Yvals[rnng-1]
                        Signal1Xvals[i]=Signal1Xvals[rnng-1]

            #Bezier interpolation
            #start from the second data until the last-2 is reached
            #B0=Di-1, B1=Di, B2=Di+1, B3=Di+2
            #S(t)=B0+(-5.5*B0+9.0*B1-4.5*B2+B3)*u
            #            +(9.0*B0-22.5*B1+18.0*B2-4.5*B3)*u*u
            #            +(-4.5*B0+13.5*B1-13.5*B2+4.5*B3)*u*u*u
            #

            #convolution filtering
            #10 data possibly be okay!
            
                        
        if ActiveTrace==1:
            Trace2Header['state']=TraceSngl
            Trace2Header['visible']=1
            Trace2Header['tracetype']=TraceSngl
            Trace2Header['sampling']=samplingrate
            Trace2Header['range']=4096
            Trace2Header['pulse']=0
            Trace2Header['gain']=0
            Trace2Header['trigger']=0
            Trace2Header['multiple']=0

            Signal2Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(2):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=float(splittedText[i])
                        zi=i
                        Signal2Yvals[i]=z
                        Signal2Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal2Yvals[i]=Signal2Yvals[rnng-1]
                        Signal2Xvals[i]=Signal2Xvals[rnng-1]                 

        if ActiveTrace==2:
            Trace3Header['state']=TraceSngl
            Trace3Header['visible']=1
            Trace3Header['tracetype']=TraceSngl
            Trace3Header['sampling']=samplingrate
            Trace3Header['range']=4096
            Trace3Header['pulse']=0
            Trace3Header['gain']=0
            Trace3Header['trigger']=0
            Trace3Header['multiple']=0

            Signal3Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(3):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        zi=i
##                        if i%2==1:
##                            z=int(splittedText[i-1])
##                            zi=i-1
                        Signal3Yvals[i]=z
                        Signal3Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal3Yvals[i]=Signal3Yvals[rnng-1]
                        Signal3Xvals[i]=Signal3Xvals[rnng-1]
    except:
        pass

def ACQFunction_RIGOL(): #this is for TDR 19.2 MHz
    global OnlineMode
    global ser
    global LTDRPulse
    global LTDRGain
    global Trace1Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    global samplingrate
    global deviceDescription
    global deviceDescription2
    global visa_address
    global rm

    #visa_address = 'USB0::0x1AB1::0x0588::DS1EB142204615::INSTR'
    #rm = visa.ResourceManager()
    scope = rm.open_resource(visa_address)
    scope.timeout = 10000 # ms
    scope.encoding = 'latin_1'
    scope.write_termination = None

    #set time/div to 100ns per division    initiate
    scope.write(':TIMebase:SCALe .0000001')
    time.sleep(0.25)
    scope.write(':TIMebase:OFFSet .0000005')
    time.sleep(0.25)

    #set voltage scale
    scope.write(':CHAN1:SCALe 2')
    time.sleep(0.25)
    #set vertical offset
    scope.write(':CHAN1:OFFS -2')
    time.sleep(0.25)
    #set bandwidth
    scope.write(':CHAN1:BWLimit OFF')
    time.sleep(0.25)
    

     #re RUN
    scope.write(':RUN')

    if deviceDescription2[:4]=="F411":
        txt='capture\n'
        res= txt.encode()
        ser.write(res)
        Txtmsg=ser.readline()
        print('TDR capture answer:',Txtmsg)

    i=0
    while scope.query(':TRIG:STAT?')!="STOP":
        print('RUNNING')
        time.sleep(1.0)
        i+=1
        if i>5:
            print('TIME OUT!')
            break
        
    print('STOPPED')

##    scope.write('::WAV:POIN:MODE NORM')
##    time.sleep(1.0)
##    print('WAVeform:POINts:MODE:',scope.query(':WAVeform:POINts:MODE?'))

    print('WAVeform:DATA:',scope.query(':WAVeform:DATA?'))
    a=scope.query(':WAVeform:DATA? CHAN1')
    #exit from remote mode
    scope.write(':KEY:FORCe')

    #print(a)
    L=[ str(255-ord(eachchar)) for eachchar in a]
    print('number of samples',len(L))
    samplingrate=1
    samplestart=10+16384//2-300
    Txtmsg="\n".join(L[10+8192-300::samplingrate])
    L=Txtmsg.split("\n")
    length=len(L)
    if length>4096:length=4096
    Txtmsg="\n".join(L[:length])
    
##    samplelen=(16394-samplestart)/samplingrate
##    if samplelen>4096: samplelen=4096
##    Txtmsg="\n".join(L[10+8192-300:10+samplelen*samplingrate:samplingrate])
##    print (Txtmsg[:40])

    #return

    if 1:        

##        txt='read\n'
##        res= txt.encode()
##        ser.write(res)
##        time.sleep(0.1)
##        Txtmsg=ser.readline()                       #timeout veya \n gelene kadar bekliyor
##        #splittedText=Txtmsg.split()

        splittedText=Txtmsg.split()
                               
        if ActiveTrace==0:
            Trace1Header['state']=TraceSngl
            Trace1Header['visible']=1
            Trace1Header['tracetype']=TraceSngl
            Trace1Header['sampling']=samplingrate
            Trace1Header['range']=4096
            Trace1Header['pulse']=0
            Trace1Header['gain']=0
            Trace1Header['trigger']=0
            Trace1Header['multiple']=0

            Signal1Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(1):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=float(splittedText[i])
##                        if 1:
##                        #if i%2==1:
##                            z=.5*float(splittedText[i-1])+.5*float(splittedText[i+1])
                        zi=i
                        Signal1Yvals[i]=z
                        Signal1Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal1Yvals[i]=Signal1Yvals[rnng-1]
                        Signal1Xvals[i]=Signal1Xvals[rnng-1]

            #Bezier interpolation
            #start from the second data until the last-2 is reached
            #B0=Di-1, B1=Di, B2=Di+1, B3=Di+2
            #S(t)=B0+(-5.5*B0+9.0*B1-4.5*B2+B3)*u
            #            +(9.0*B0-22.5*B1+18.0*B2-4.5*B3)*u*u
            #            +(-4.5*B0+13.5*B1-13.5*B2+4.5*B3)*u*u*u
            #

            #convolution filtering
            #10 data possibly be okay!
            
                        
        if ActiveTrace==1:
            Trace2Header['state']=TraceSngl
            Trace2Header['visible']=1
            Trace2Header['tracetype']=TraceSngl
            Trace2Header['sampling']=samplingrate
            Trace2Header['range']=4096
            Trace2Header['pulse']=0
            Trace2Header['gain']=0
            Trace2Header['trigger']=0
            Trace2Header['multiple']=0

            Signal2Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(2):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=float(splittedText[i])
                        zi=i
                        Signal2Yvals[i]=z
                        Signal2Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal2Yvals[i]=Signal2Yvals[rnng-1]
                        Signal2Xvals[i]=Signal2Xvals[rnng-1]                 

        if ActiveTrace==2:
            Trace3Header['state']=TraceSngl
            Trace3Header['visible']=1
            Trace3Header['tracetype']=TraceSngl
            Trace3Header['sampling']=samplingrate
            Trace3Header['range']=4096
            Trace3Header['pulse']=0
            Trace3Header['gain']=0
            Trace3Header['trigger']=0
            Trace3Header['multiple']=0

            Signal3Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(3):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        zi=i
                        Signal3Yvals[i]=z
                        Signal3Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal3Yvals[i]=Signal3Yvals[rnng-1]
                        Signal3Xvals[i]=Signal3Xvals[rnng-1]            

def ACQFunction_3050_ALL():
    global ActiveTrace
    global Trace1Header
    global Trace2Header
    global Trace3Header
    
    if ActiveTrace==0:
        if Trace1Header['state']==TraceSngl or Trace1Header['state']==TraceWithTrig:
            ACQFunction_3050_Single()
    elif ActiveTrace==1:
        if Trace2Header['state']==TraceSngl or Trace2Header['state']==TraceWithTrig:
            ACQFunction_3050_Single()
    elif ActiveTrace==2:
        if Trace3Header['state']==TraceSngl or Trace3Header['state']==TraceWithTrig:
            ACQFunction_3050_Single()
    
def ACQFunction_3050_Single(): 
    global OnlineMode
    global ser
    global LTDRPulse
    global LTDRGain
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    global PulseWidth
    global Gain

    print('OnlineMode:',OnlineMode)

    usedpulsetxt='pulse='+str(PulseWidth)+'\n'
    usedgaintxt='gain='+str(64-Gain)+'\n'
    print(usedpulsetxt.encode())
    print(usedgaintxt.encode())
    
    if (ActiveTrace==0 and Trace1Header['state']==TraceWithTrig) or \
       (ActiveTrace==1 and Trace2Header['state']==TraceWithTrig) or \
       (ActiveTrace==2 and Trace3Header['state']==TraceWithTrig):
        trigonselected=1
    else:
        trigonselected=0
            
    if OnlineMode==2:
        ser.reset_input_buffer()
        ser.write( 'ver\n'.encode())
        Txtmsg=ser.readline()
        print(str(Txtmsg))
        
        #send pulse info
        ser.reset_input_buffer()
        ser.write(usedpulsetxt.encode())
        Txtmsg=ser.readline()
        #send gain info
        ser.reset_input_buffer()
        ser.write(usedgaintxt.encode())
        Txtmsg=ser.readline()
        
        #send trig info
        ser.reset_input_buffer()
        if trigonselected==1:
            ser.write( 'trigon\n'.encode())
        else:
            ser.write( 'trigoff\n'.encode())
        Txtmsg=ser.readline()
        print('trigonselected:',trigonselected)
            
        #send capture command
        ser.reset_input_buffer()
        ser.write( 'capture\n'.encode())
        Txtmsg=ser.readline()
        print('capture response:',Txtmsg)

        timeoutctr=40
        #check if capture finished
        ser.write('finish?\n'.encode())
        Txtmsg=ser.readline()
        print('finish? response:',Txtmsg)
        print(Txtmsg.split(b'\n')[0])
        while Txtmsg.split(b'\n')[0]!=b'OK':
            ser.write('finish?\n'.encode())
            Txtmsg=ser.readline()
            time.sleep(0.25)
            timeoutctr-=1
            if timeoutctr==0:
                break
            print(Txtmsg)
            print(Txtmsg.split(b'\n')[0])

        if timeoutctr==0:
            return    

            
        #read signal data
        ser.write('read\n'.encode())
        #sleep(1)
        Txtmsg=ser.readline() #timeout veya \n gelene kadar bekliyor

        if ActiveTrace==0:
            if Trace1Header['state']==TraceSngl:
                Trace1Header['tracetype']=TraceSngl
            elif Trace1Header['state']==TraceMult:
                Trace1Header['tracetype']=TraceSngl
            elif Trace1Header['state']==TraceWithTrig:
                Trace1Header['tracetype']=TraceWithTrig
            Trace1Header['visible']=1
            Trace1Header['range']=4096
            Trace1Header['pulse']=PulseWidth
            Trace1Header['gain']=Gain
            Trace1Header['trigger']=0
            Trace1Header['multiple']=0

            Signal1Yvals=np.zeros(4096)
            splittedText=Txtmsg.split()
            rnng=len(splittedText)
            print('Number of  Data Received(1):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        Signal1Yvals[i]=z
                        Signal1Xvals[i]=i*samplingrate*1E-9
                    else:
                        Signal1Yvals[i]=Signal1Yvals[rnng-1]
                        Signal1Xvals[i]=Signal1Xvals[rnng-1]
                        
        if ActiveTrace==1:
            if Trace2Header['state']==TraceSngl:
                Trace2Header['tracetype']=TraceSngl
            elif Trace2Header['state']==TraceMult:
                Trace2Header['tracetype']=TraceSngl
            elif Trace2Header['state']==TraceWithTrig:
                Trace2Header['tracetype']=TraceWithTrig
            Trace2Header['visible']=1
            Trace2Header['range']=4096
            Trace1Header['pulse']=PulseWidth
            Trace1Header['gain']=Gain
            Trace2Header['trigger']=0
            Trace2Header['multiple']=0

            Signal2Yvals=np.zeros(4096)
            splittedText=Txtmsg.split()
            rnng=len(splittedText)
            print('Number of  Data Received(2):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        Signal2Yvals[i]=z
                        Signal2Xvals[i]=i*samplingrate*1E-9
                    else:
                        Signal2Yvals[i]=Signal2Yvals[rnng-1]
                        Signal2Xvals[i]=Signal2Xvals[rnng-1]                    

        if ActiveTrace==2:
            if Trace3Header['state']==TraceSngl:
                Trace3Header['tracetype']=TraceSngl
            elif Trace3Header['state']==TraceMult:
                Trace3Header['tracetype']=TraceSngl
            elif Trace3Header['state']==TraceWithTrig:
                Trace3Header['tracetype']=TraceWithTrig
            Trace3Header['visible']=1
            Trace3Header['range']=4096
            Trace1Header['pulse']=PulseWidth
            Trace1Header['gain']=Gain
            Trace3Header['trigger']=0
            Trace3Header['multiple']=0

            Signal3Yvals=np.zeros(4096)
            splittedText=Txtmsg.split()
            rnng=len(splittedText)
            print('Number of  Data Received(3):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        Signal3Yvals[i]=z
                        Signal3Xvals[i]=i*samplingrate*1E-9
                    else:
                        Signal3Yvals[i]=Signal3Yvals[rnng-1]
                        Signal3Xvals[i]=Signal3Xvals[rnng-1]

def ACQFunction_USON(): #this is for Ultrasonic with double receiver
    global OnlineMode
    global ser
    global LTDRPulse
    global LTDRGain
    global Trace1Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    global samplingrate

    if OnlineMode==0:
        return()
    
    if OnlineMode==2:            
        ser.reset_input_buffer()

        print ("uson sampling rate:",samplingrate)
##        if CBoxPulseVar.get()==0:
##            ser.reset_input_buffer()
##            txt='p0\n'
##            res= txt.encode()
##            ser.write(res)
##            sleep(1)
##        else:
##            ser.reset_input_buffer()
##            txt='p1\n'
##            res= txt.encode()
##            ser.write(res)
##            sleep(1)            
        
        txt='a\n'
        res= txt.encode()
        ser.write(res)
        time.sleep(0.1)
        Txtmsg=ser.readline()                       #timeout veya \n gelene kadar bekliyor

        print('Number of characters Received(1):',len(Txtmsg));
        splittedText=Txtmsg.split()
        if ActiveTrace==0:
            
            Trace1Header['state']=TraceSngl
            Trace1Header['visible']=1
            Trace1Header['tracetype']=TraceSngl
            Trace1Header['sampling']=samplingrate
            Trace1Header['range']=4096
            Trace1Header['pulse']=0
            Trace1Header['gain']=0
            Trace1Header['trigger']=0
            Trace1Header['multiple']=0

            Signal1Yvals=np.zeros(8192)
            Signal1Xvals=np.zeros(8192)    
            rnng=len(splittedText)
            if rnng>=256:
                for i in range(8192):
                    if i<rnng:
                        z=float(splittedText[i])
                        zi=i
                        Signal1Yvals[i]=z
                        Signal1Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal1Yvals[i]=Signal1Yvals[rnng-1]
                        Signal1Xvals[i]=Signal1Xvals[rnng-1]

                for i in range(1,8190,2):
                        Signal1Yvals[i]=0.5*(Signal1Yvals[i-1]+Signal1Yvals[i+1])

        #Bezier interpolation
            #start from the second data until the last-2 is reached
            #B0=Di-1, B1=Di, B2=Di+1, B3=Di+2
            #S(t)=B0+(-5.5*B0+9.0*B1-4.5*B2+B3)*u
            #            +(9.0*B0-22.5*B1+18.0*B2-4.5*B3)*u*u
            #            +(-4.5*B0+13.5*B1-13.5*B2+4.5*B3)*u*u*u
            #

            #convolution filtering
            #10 data possibly be okay!
            
                        
        if ActiveTrace==1:
            Trace2Header['state']=TraceSngl
            Trace2Header['visible']=1
            Trace2Header['tracetype']=TraceSngl
            Trace2Header['sampling']=samplingrate
            Trace2Header['range']=4096
            Trace2Header['pulse']=0
            Trace2Header['gain']=0
            Trace2Header['trigger']=0
            Trace2Header['multiple']=0

            Signal2Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(2):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=float(splittedText[i])
                        zi=i
                        Signal2Yvals[i]=z
                        Signal2Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal2Yvals[i]=Signal2Yvals[rnng-1]
                        Signal2Xvals[i]=Signal2Xvals[rnng-1]                 

        if ActiveTrace==2:
            Trace3Header['state']=TraceSngl
            Trace3Header['visible']=1
            Trace3Header['tracetype']=TraceSngl
            Trace3Header['sampling']=samplingrate
            Trace3Header['range']=4096
            Trace3Header['pulse']=0
            Trace3Header['gain']=0
            Trace3Header['trigger']=0
            Trace3Header['multiple']=0

            Signal3Yvals=np.zeros(4096)
            
            rnng=len(splittedText)
            print('Number of  Data Received(3):',rnng);
            if rnng<256:
                print('Data Received:',Txtmsg);
            if rnng>=256:
                for i in range(4096):
                    if i<rnng:
                        z=int(splittedText[i])
                        zi=i
##                        if i%2==1:
##                            z=int(splittedText[i-1])
##                            zi=i-1
                        Signal3Yvals[i]=z
                        Signal3Xvals[i]=zi*samplingrate*1E-9
                    else:
                        Signal3Yvals[i]=Signal3Yvals[rnng-1]
                        Signal3Xvals[i]=Signal3Xvals[rnng-1] 
                        

def disableButtons(ActiveButton):
    global trcBtns
    
    for i in range(3):
        if ActiveButton!=i:
            trcBtns[i].configure(state=DISABLED)
    for i in range(5):
        if ActiveButton!=(i+3):
            menuBtns[i].configure(state=DISABLED)
    for i in range(6):
        if ActiveButton!=(i+8):
            taskBtns[i].configure(state=DISABLED)

def enableButtons(ActiveButton):
    for i in range(3):
        if ActiveButton==-1 or ActiveButton==i:
            trcBtns[i].configure(state=NORMAL)
    for i in range(5):
        if ActiveButton==-1 or ActiveButton==(i+3):
            menuBtns[i].configure(state=NORMAL)
    for i in range(6):
        if ActiveButton==-1 or ActiveButton==(i+8):
            if len(taskBtns[i]['text'])!=0:
                if taskBtns[i]['text'][-1]!='*':
                    taskBtns[i].configure(state=NORMAL)
                              
def selectTrcFunction(s):
    global ActiveButton
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    global trcBtns

    if s==0:
        if ActiveTrace==0:
            if Trace1Header['state']==TraceEmpty:
                Trace1Header['state']=TraceSngl
                Trace1Header['visible']=1
                trcBtns[s].configure(bg = "yellow")
            elif Trace1Header['state']==TraceSngl:
##                Trace1Header['state']=TraceMult
##                Trace1Header['visible']=1
##                trcBtns[s].configure(bg = "yellow")
##            elif Trace1Header['state']==TraceMult:
                Trace1Header['state']=TraceWithTrig
                Trace1Header['visible']=1
                trcBtns[s].configure(bg = "yellow")
            elif Trace1Header['state']==TraceWithTrig:
                Trace1Header['state']=TraceEmpty
                Trace1Header['visible']=0
                trcBtns[s].configure(bg = "gray")
            updateTraceButtons()
        else:
            if Trace1Header['visible']==0:
                Trace1Header['visible']=1
            else:
                Trace1Header['visible']=0
                
    if s==1:
        if ActiveTrace==1:
            trcBtns[s].configure(bg = "yellow")
            if Trace2Header['state']==TraceEmpty:
                Trace2Header['state']=TraceSngl
                Trace2Header['visible']=1
            elif Trace2Header['state']==TraceSngl:
##                Trace2Header['state']=TraceMult
##                Trace2Header['visible']=1
##            elif Trace2Header['state']==TraceMult:
                Trace2Header['state']=TraceWithTrig
                Trace2Header['visible']=1
            elif Trace2Header['state']==TraceWithTrig:
                Trace2Header['state']=TraceEmpty
                Trace2Header['visible']=0
            updateTraceButtons()
        else:
            if Trace2Header['visible']==0:
                Trace2Header['visible']=1
            else:
                Trace2Header['visible']=0

    if s==2:
        if ActiveTrace==2:
            trcBtns[s].configure(bg = "yellow")
            if Trace3Header['state']==TraceEmpty:
                Trace3Header['state']=TraceSngl
                Trace3Header['visible']=1
            elif Trace3Header['state']==TraceSngl:
##                Trace3Header['state']=TraceMult
##                Trace3Header['visible']=1
##            elif Trace3Header['state']==TraceMult:
                Trace3Header['state']=TraceWithTrig
                Trace3Header['visible']=1
            elif Trace3Header['state']==TraceWithTrig:
                Trace3Header['state']=TraceEmpty
                Trace3Header['visible']=0
            updateTraceButtons()
        else:
            if Trace3Header['visible']==0:
                Trace3Header['visible']=1
            else:
                Trace3Header['visible']=0
    enableButtons(ActiveButton)
    updateTraceButtons()
    UpdateDisplay()

##def copyTraceParameters(s,d):
##    global Trace1Header
##    global Trace2Header
##    global Trace3Header
##
##    mylist = thislist.copy()
##    for i in range(Trace1Header

def updateTraceButtons():
    global ActiveTrace


    if Trace1Header['visible']==0:
         trcBtns[0].configure(bg='gray')
    else:
         trcBtns[0].configure(bg='red')
    if Trace2Header['visible']==0:
         trcBtns[1].configure(bg='gray')
    else:
         trcBtns[1].configure(bg='red')
    if Trace3Header['visible']==0:
         trcBtns[2].configure(bg='gray')
    else:
         trcBtns[2].configure(bg='red')

    if ActiveTrace==0:
        trcBtns[0].configure(bg='yellow')
        if Trace1Header['state']==TraceEmpty:
            trcBtns[0].configure(text="1\nEMPTY")
        elif Trace1Header['state']==TraceSngl:
            trcBtns[0].configure(text="1\nSNGL")
        elif Trace1Header['state']==TraceMult:
            trcBtns[0].configure(text="1\nMULT")
        elif Trace1Header['state']==TraceWithTrig:
            trcBtns[0].configure(text="1\nTRIG")
    else:    
        if Trace1Header['tracetype']==TraceEmpty:
            trcBtns[0].configure(text="1\nEMPTY")
        elif Trace1Header['tracetype']==TraceSngl:
            trcBtns[0].configure(text="1\nSNGL")
        elif Trace1Header['tracetype']==TraceMult:
            trcBtns[0].configure(text="1\nMULT")
        elif Trace1Header['tracetype']==TraceWithTrig:
            trcBtns[0].configure(text="1\nTRIG")
        
    if ActiveTrace==1:
        trcBtns[1].configure(bg='yellow')
        if Trace2Header['state']==TraceEmpty:
            trcBtns[1].configure(text="2\nEMPTY")
        elif Trace2Header['state']==TraceSngl:
            trcBtns[1].configure(text="2\nSNGL")
        elif Trace2Header['state']==TraceMult:
            trcBtns[1].configure(text="2\nMULT")
        elif Trace2Header['state']==TraceWithTrig:
            trcBtns[1].configure(text="2\nTRIG")
    else:    
        if Trace2Header['tracetype']==TraceEmpty:
            trcBtns[1].configure(text="2\nEMPTY")
        elif Trace2Header['tracetype']==TraceSngl:
            trcBtns[1].configure(text="2\nSNGL")
        elif Trace2Header['tracetype']==TraceMult:
            trcBtns[1].configure(text="2\nMULT")
        elif Trace2Header['tracetype']==TraceWithTrig:
            trcBtns[1].configure(text="2\nTRIG")
            
    if ActiveTrace==2:
        trcBtns[2].configure(bg='yellow')
        if Trace3Header['state']==TraceEmpty:
            trcBtns[2].configure(text="3\nEMPTY")
        elif Trace3Header['state']==TraceSngl:
            trcBtns[2].configure(text="3\nSNGL")
        elif Trace3Header['state']==TraceMult:
            trcBtns[2].configure(text="3\nMULT")
        elif Trace3Header['state']==TraceWithTrig:
            trcBtns[2].configure(text="3\nTRIG")
    else:    
        if Trace3Header['tracetype']==TraceEmpty:
            trcBtns[2].configure(text="3\nEMPTY")
        elif Trace3Header['tracetype']==TraceSngl:
            trcBtns[2].configure(text="3\nSNGL")
        elif Trace3Header['tracetype']==TraceMult:
            trcBtns[2].configure(text="3\nMULT")
        elif Trace3Header['tracetype']==TraceWithTrig:
            trcBtns[2].configure(text="3\nTRIG")
            
def selectMenuFunction(menuBtn):
    global ActiveButton
    global ActiveMenu
    global selectedComport
    global ActiveTrace
    global instrument
    global samplingrate
    global deviceDescription
    global deviceDescription2

    disableButtons(ActiveButton)
    ActiveMenu=menuBtn
    
    if menuBtns[menuBtn].cget('bg')=='yellow':
        pass
    else:
        for i in range(5):
            if i==menuBtn:
                menuBtns[i].configure(bg = "yellow",activebackground='yellow')
            else:
                menuBtns[i].configure(bg = "red",activebackground='red')

    if menuBtn==0:
        taskBtns[0].configure(state=NORMAL,bg = "red", fg="black", text="RANGE \n-")
        taskBtns[1].configure(state=NORMAL,bg = "red", fg="black", text="RANGE \n+")
        taskBtns[2].configure(state=NORMAL,bg = "red", fg="black", text="SHIFT \n-")
        taskBtns[3].configure(state=NORMAL,bg = "red", fg="black", text="SHIFT \n+")
        taskBtns[4].configure(state=DISABLED, bg = "blue", fg="blue", text='')
        taskBtns[5].configure(state=DISABLED, bg = "blue", fg="blue", text='')          

    if menuBtn==1:
        taskBtns[0].configure(state=NORMAL,bg = "red", fg="black", text="MARKER1\n<< >>")
        taskBtns[1].configure(state=NORMAL,bg = "red", fg="black", text="MARKER2\n<< >>")
        taskBtns[2].configure(state=NORMAL,bg = "red", fg="black", text="v/2\n<< >>")
        taskBtns[3].configure(state=DISABLED, bg = "blue", fg="blue", text='') 
        if meters_time==0:
            taskBtns[4].configure(state=DISABLED, bg = "red", fg="black",
                                  text= 'displaying\n in meters')
        else:
            taskBtns[4].configure(state=DISABLED, bg = "red", fg="black",
                                  text= 'displaying\n in time')    
        taskBtns[5].configure(state=DISABLED, bg = "red", fg="black",
                                  text= 'sampling:'+'\n'+str(samplingrate)+'ns  *')        
    if menuBtn==2:
        taskBtns[0].configure(state=NORMAL,bg = "red", fg="black", text="PULSE\n-")
        taskBtns[1].configure(state=NORMAL,bg = "red", fg="black", text="PULSE\n+")
        taskBtns[2].configure(state=NORMAL,bg = "red", fg="black", text="GAIN\n-")
        taskBtns[3].configure(state=NORMAL,bg = "red", fg="black", text="GAIN\n+")

        taskBtns[4].configure(state=NORMAL,bg = "red", fg="black", text="CAPTURE\nto  : ("+str(ActiveTrace+1)+")") #"CAPTURE\n(NO TRIG.)"
        taskBtns[5].configure(state=NORMAL,bg = "red", fg="black", text="CHANGE\nTRACE") #"CAPTURE\n(NO TRIG.)"

    if menuBtn==3: #FILE MENU SELECTED
        taskBtns[0].configure(state=NORMAL,bg = "red", fg="black", text="SAVE\nTRACES")
        taskBtns[1].configure(state=DISABLED,bg = "red", fg="black", text="LOAD\nTRACES")
        taskBtns[2].configure(state=DISABLED, bg = "red", fg="black", text='COMPUTE\nS1=S2-S3')
        taskBtns[3].configure(state=DISABLED, bg = "red", fg="black", text='COMPUTE\nS1=S2, S2=S1')
        taskBtns[4].configure(state=DISABLED, bg = "red", fg="black", text='COMPUTE\nS1=S3, S3=S1')
        taskBtns[5].configure(state=DISABLED,bg = "red", fg="black", text="S3=\nHIGHRES(S1)")

    if menuBtn==4: #SETUP MENU SELECTED
        taskBtns[0].configure(state=DISABLED,bg = "red", fg="black", text=deviceDescription) #"NO\nDEVICE*"
        #DetectConnectedDevices()
        taskBtns[1].configure(state=DISABLED, bg = "red", fg="black", text= ' ')
        taskBtns[2].configure(state=DISABLED, bg = "red", fg="black", text='SERIAL\n'+selectedComport+'*') #selectedComport
        taskBtns[3].configure(state=DISABLED, bg = "red", fg="black", text='TERMINATE') #
        taskBtns[4].configure(state=NORMAL,bg = "red", fg="black", text="SAVE\nSETUP") #
        taskBtns[5].configure(state=DISABLED,bg = "red", fg="black", text="LOAD\nSETUP*") #

    enableButtons(ActiveButton)

def updateMarkerPositions():
    global Marker1Pos
    global Marker2Pos
    global ViewStart
    global ViewRange
    global MarkerLine1
    global MarkerLine2

##    Marker1Pos=25
##    Marker2Pos=200
##    print('viewstart:',ViewStart)
##    print('viewrange:',ViewRange)
    
    if Marker1Pos<ViewStart or Marker1Pos>(ViewStart+ViewRange): #out of screen
        MarkerLine1.place(x=-1, y=160)
        print('xplaceout')
    else:
        xscale=ViewRange/660
        xplace=95+(Marker1Pos-ViewStart)/xscale
##        print('xplace:',xplace)
        MarkerLine1.place(x=xplace, y=160)
        
    if Marker2Pos<ViewStart or Marker2Pos>(ViewStart+ViewRange): #out of screen
        MarkerLine2.place(x=-1, y=160)
    else:
        xscale=ViewRange/660
        xplace=95+(Marker2Pos-ViewStart)/xscale
        MarkerLine2.place(x=xplace, y=160)
##    print('xscale:',ViewRange/660)
##    print('marker positions:',Marker1Pos,Marker2Pos)
##    gui.update()
    
def selectTaskFunction(taskno):
    global ViewRange
    global ViewStart
    global ActiveButton
    global ActiveMenu
    global firstmousepntx
    global PulseWidths
    global PulseWidth
    global Gain
    global mycanvas3
    global ActiveTrace
    global OnlineMode
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global PulseWidth
    global Gain
    global Marker1Pos
    global Marker2Pos
    global tdrwd
    global meters_time

    disableButtons(ActiveButton)
    taskBtns[taskno].configure(bg = "yellow")
    gui.update()
    
    if ActiveMenu==0: # change viewrange
        if taskno==0:
            ViewRange=round(ViewRange*0.75,0)
            if ViewRange<20.0: ViewRange=20.0
##            if ViewRange==50: ViewRange=20
##            if ViewRange==100: ViewRange=50
##            if ViewRange==200: ViewRange=100
##            if ViewRange==500: ViewRange=200
##            if ViewRange==1000: ViewRange=500
##            if ViewRange==2000: ViewRange=1000
##            if ViewRange==5000: ViewRange=2000
            rangeLbl.configure(text='RANGE: '+str(ViewRange)+'m')
            UpdateDisplay()
            dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')
        if taskno==1:
            ViewRange=round(ViewRange/0.75,0)
            if ViewRange>20000.0: ViewRange=5000.0
##            if ViewRange==2000: ViewRange=5000
##            if ViewRange==1000: ViewRange=2000
##            if ViewRange==500: ViewRange=1000
##            if ViewRange==200: ViewRange=500
##            if ViewRange==100: ViewRange=200
##            if ViewRange==50: ViewRange=100
##            if ViewRange==20: ViewRange=50
            rangeLbl.configure(text='RANGE: '+str(ViewRange)+'m')
            UpdateDisplay()
            dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')
        if taskno==2: # shift traces
            ViewStart-=ViewRange/20
            if ViewStart<0: ViewStart=0
            UpdateDisplay()
        if taskno==3:
            ViewStart+=ViewRange/20
            if (ViewStart+ViewRange)>5000:
                ViewStart=5000-ViewRange
            UpdateDisplay()
                          

    if ActiveMenu==1 : # change marker location
        if taskno==0: #marker1
            if ActiveButton==-1:
                ActiveButton=8
                firstmousepntx=-1
                
##                mycanvas3.bind ("<Button-1>", startcallbackdown)
                gui.bind ("<B1-Motion>", startcallbackmove)
                gui.bind ("<ButtonRelease-1>", startcallbackup)
            else:
                ActiveButton=-1
##                gui.unbind ("<B1-Motion>")
##                gui.unbind ("<ButtonRelease-1>")
                UpdateDisplay()
                          
        if taskno==1: #marker2
            if ActiveButton==-1:
                ActiveButton=9
                firstmousepntx=-1
                gui.bind ("<B1-Motion>", startcallbackmove)
                gui.bind ("<ButtonRelease-1>", startcallbackup)       
            else:
                ActiveButton=-1
##                gui.unbind ("<B1-Motion>")
##                gui.unbind ("<ButtonRelease-1>")
                UpdateDisplay()
            
        if taskno==2: #v/2
            if ActiveButton==-1:
                ActiveButton=10
                gui.bind ("<B1-Motion>", startcallbackmove)
                gui.bind ("<ButtonRelease-1>", startcallbackup) 
            else:
                ActiveButton=-1
##                gui.unbind ("<B1-Motion>")
                UpdateDisplay()

        if taskno==3: 
            pass

        if taskno==4: #meters_time
            if meters_time==1:
                meters_time=0
                taskBtns[4].configure(state=DISABLED, bg = "red", fg="black",
                                      text= 'displaying\n in meters')
            else:
                meters_time=1
                taskBtns[4].configure(state=DISABLED, bg = "red", fg="black",
                                      text= 'displaying\n in time')
        if taskno==5: #sampling
            pass
##            taskBtns[5].configure(state=DISABLED, bg = "red", fg="black",
##                                      text= 'sampling:'+'\n'+str(samplingrate)+'ns')  
                
    if ActiveMenu==2 : #
        if taskno==0: #pulse -
            if PulseWidth>0:
                PulseWidth-=1
                pwLbl.configure(text=PulseWidths[PulseWidth])
        if taskno==1: #pulse +
            if PulseWidth<7:
                PulseWidth+=1
                pwLbl.configure(text=PulseWidths[PulseWidth])
        if taskno==2: #gain-
            if Gain>0:
                Gain-=1
                gainLbl.configure(text='Gain: '+str(Gain))
        if taskno==3: #gain+
            if Gain<63:
                Gain+=1
                gainLbl.configure(text='Gain: '+str(Gain))
        if taskno==4: #capture
            if OnlineMode==0:
                print('offline mode')

            if deviceDescription[:4]=='F411':
                ACQFunction_F411()
            elif deviceDescription[:8]=="Ultrason":
                disableButtons(-1)
                gui.update()
                ACQFunction_USON()
                enableButtons(ActiveButton)
                gui.update()
            
            elif deviceDescription[:5]=='RIGOL':
                disableButtons(-1)
                gui.update()
                ACQFunction_RIGOL()
                enableButtons(ActiveButton)
                gui.update()                
            else:
                ACQFunction_3050_ALL()
            updateTraceButtons()
            UpdateDisplay()
            
        if taskno==5: #change trace
            if ActiveTrace==0:
                Trace1Header['state']=Trace1Header['tracetype']
                ActiveTrace=1
                Trace2Header['state']=TraceSngl
                #Trace2Header['visible']==1
            elif ActiveTrace==1:
                Trace2Header['state']=Trace2Header['tracetype']
                ActiveTrace=2
                Trace3Header['state']=TraceSngl
                #Trace3Header['visible']==1
            elif ActiveTrace==2:
                ActiveTrace=3
                Trace3Header['state']=Trace3Header['tracetype']
            elif ActiveTrace==3:
                ActiveTrace=0
                Trace1Header['state']=TraceSngl
                #Trace1Header['visible']==1
                
            if ActiveTrace<3:
                taskBtns[4].configure(text="CAPTURE\nto  : ("+str(ActiveTrace+1)+")")
            else:
                taskBtns[4].configure(text="CAPTURE\nto  : (NONE)")
                    
            updateTraceButtons()
            UpdateDisplay()

    if ActiveMenu==3 : #FILE MENU BUTTON ACTIVATED
        if taskno==0: #save traces
            saveALLData()
            print('save traces done!')

        if taskno==1: #load traces
            if TARGETOS=='WINDOWS':
                fulldestpath =os.getcwd()
                print('cwd:',os.getcwd())
                filename = filedialog.askopenfilename( initialdir = fulldestpath, initialfile = '.txt', \
                    defaultextension=".txt",filetypes=[("All Files","*.*"),("Text Documents",".txt")])

                if len(filename)!=0:
                        lines = [line.strip() for line in open(filename)]
                        parseLoadedData(lines)
                        updateTraceButtons()
                        UpdateDisplay()
                        #if len(lines)>10 : lines=lines[:10]
                        #messagebox.showinfo("MESSAGE1", str(lines))
            else:
                print ('load feature is not completed yet')
                messagebox.showinfo("ERROR !", "'load feature is not completed yet'")

        if taskno==2: ## S1=S2-S3
            print('processing "S1=S2-S3"')
            Trace1Header=Trace2Header.copy()
            Signal1Xvals=Signal2Xvals[:]
            for i1 in range(len(Signal1Xvals)):
                Signal1Yvals[i1]=Signal2Yvals[i1]-Signal3Yvals[i1]+10       
            UpdateDisplay()
            print('"S1=S2-S3"  done')
            
        if taskno==3: ## S1=S2, S2=S1
            print('processing "S1=S2, S2=S1"')
            TraceHeader=Trace1Header.copy()
            Trace1Header=Trace2Header.copy()
            Trace2Header=TraceHeader.copy()

            Signal1XvalsCopy=np.zeros(len(Signal1Xvals))
            Signal1YvalsCopy=np.zeros(len(Signal1Yvals))
            for i1 in range(len(Signal1Xvals)):
                Signal1XvalsCopy[i1]=Signal1Xvals[i1]
                Signal1YvalsCopy[i1]=Signal1Yvals[i1]

            Signal1Xvals=np.zeros(len(Signal2Xvals))
            Signal1Yvals=np.zeros(len(Signal2Yvals))
            for i1 in range(len(Signal2Xvals)):
                Signal1Xvals[i1]=Signal2Xvals[i1]
                Signal1Yvals[i1]=Signal2Yvals[i1]                

            Signal2Xvals=np.zeros(len(Signal1XvalsCopy))
            Signal2Yvals=np.zeros(len(Signal1YvalsCopy))
            for i1 in range(len(Signal1XvalsCopy)):
                Signal2Xvals[i1]=Signal1XvalsCopy[i1]
                Signal2Yvals[i1]=Signal1YvalsCopy[i1]                 
            UpdateDisplay()
            print('"S1=S2, S2=S1"  done')

        if taskno==4: ## S1=S3, S3=S1
            print('processing "S1=S3, S3=S1"')
            TraceHeader=Trace1Header.copy()
            Trace1Header=Trace3Header.copy()
            Trace3Header=TraceHeader.copy()

            Signal1XvalsCopy=np.zeros(len(Signal1Xvals))
            Signal1YvalsCopy=np.zeros(len(Signal1Yvals))
            for i1 in range(len(Signal1Xvals)):
                Signal1XvalsCopy[i1]=Signal1Xvals[i1]
                Signal1YvalsCopy[i1]=Signal1Yvals[i1]

            Signal1Xvals=np.zeros(len(Signal3Xvals))
            Signal1Yvals=np.zeros(len(Signal3Yvals))
            for i1 in range(len(Signal3Xvals)):
                Signal1Xvals[i1]=Signal3Xvals[i1]
                Signal1Yvals[i1]=Signal3Yvals[i1]                

            Signal3Xvals=np.zeros(len(Signal1XvalsCopy))
            Signal3Yvals=np.zeros(len(Signal1YvalsCopy))
            for i1 in range(len(Signal1XvalsCopy)):
                Signal3Xvals[i1]=Signal1XvalsCopy[i1]
                Signal3Yvals[i1]=Signal1YvalsCopy[i1]                    
                     
            UpdateDisplay()
            print('"S1=S3, S3=S1"  done')
            
        if taskno==5: ## S3=HIGHRES(S1)
            Trace3Header=Trace1Header.copy()
            Signal3Xvals=np.zeros(4*len(Signal1Xvals))
            Signal3Yvals=np.zeros(4*len(Signal1Yvals))

            for i in range(len(Signal1Yvals)):
                Signal3Xvals[4*i]=Signal1Xvals[i]
                Signal3Yvals[4*i]=Signal1Yvals[i]
                if i==0:
                    for j in range(1,4):
                        u=0.25*j
                        Signal3Xvals[4*i+j]=(1-u)*Signal1Xvals[i]+u*Signal1Xvals[i+1]
                        Signal3Yvals[4*i+j]=(1-u)*Signal1Yvals[i]+u*Signal1Yvals[i+1]
                else:
                    try:
                        B0=Signal1Yvals[i-1]
                        B1=Signal1Yvals[i]
                        B2=Signal1Yvals[i+1]
                        B3=Signal1Yvals[i+2]
                        
                        for j in range(1,4):
                            u=0.25*j
                            Signal3Xvals[4*i+j]=(1-u)*Signal1Xvals[i]+u*Signal1Xvals[i+1]
                            u=0.333333333+0.333333333*j/4
                            Signal3Yvals[4*i+j]=B0+(-5.5*B0+9.0*B1-4.5*B2+B3)*u  +\
                                (9.0*B0-22.5*B1+18.0*B2-4.5*B3)*u*u+\
                                (-4.5*B0+13.5*B1-13.5*B2+4.5*B3)*u*u*u
                    except:
                        for j in range(1,4):
                            u=0.25*j
                            Signal3Xvals[4*i+j]=Signal1Xvals[i]
                            Signal3Yvals[4*i+j]=Signal1Yvals[i]
            UpdateDisplay()
            print('"S1=S3, S3=S1"  done')
            
    if ActiveMenu==4 : # SETUP
        if taskno==3: #terminate
            if TARGETOS=='PI':
                mediadiskpath=''
                if os.path.exists('/media/pi/WORK'):
                    mediadiskpath='/media/pi/WORK'
                elif os.path.exists('/media/gd/WORK'):
                    mediadiskpath='/media/gd/WORK'

                print("media found:",mediadiskpath)
                if len(mediadiskpath)>0:
                    sourcefile=os.path.join(mediadiskpath,'LTGTDR.py')
                    if os.path.exists(sourcefile):
                        destfile=os.path.join(tdrwd,'LTGTDR.py')
                        path = shutil.copy(sourcefile,destfile) 
                        print(path)

            plt.close()
            gui.destroy()
            return()
        if taskno==4: #save setup
            writeCurrentSetup()
                    
##    UpdateDisplay()
    if ActiveButton==-1:
        taskBtns[taskno].configure(bg = "red")


    enableButtons(ActiveButton)

def startcallbackmove(event):
    global ActiveButton
    global PVeloc05Metric
    global firstmousepntx
    
    xx= event.x  #766 106
    yy=event.y
    if xx>=6 and xx<=866 and yy<340:
        if ActiveButton==8:
            if firstmousepntx==-1:
                if xx<106:xx=106
                if xx>766: xx=766
                firstmousepntx=xx
            else:
                xx=(firstmousepntx+xx)/2
                if xx<106:xx=106
                if xx>766: xx=766
            MarkerLine1.place(x=xx-10, y=160)
            dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')

        elif ActiveButton==9:
            if firstmousepntx==-1:
                if xx<105:xx=106
                if xx>766: xx=766                
                firstmousepntx=xx
            else:
                xx=(firstmousepntx+xx)/2
                if xx<106:xx=106
                if xx>766: xx=766
            MarkerLine2.place(x=xx-10, y=160)
            dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')
        elif ActiveButton==10:
            if xx<105:xx=106
            if xx>766: xx=766
            PVeloc05Metric=50+0.7*(xx-106)/6.60
            pvLbl.configure(text='v/2: '+str(round(PVeloc05Metric,0)) +'m/us') #Label(gui, text="v/2: 100m/us", font="Helvetica 14")
            dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')
        #print ("x:", xx-106,event.y)


def startcallbackdown(event):
    global ActiveButton
    global PVeloc05Metric
    global firstmousepntx
    global mycanvas2
    
    #mycanvas2.bind ("<B1-Motion>", startcallbackmove)
    
def startcallbackup(event):
    global ActiveButton
    global PVeloc05Metric
    global firstmousepntx
    global mycanvas2
    global Marker1Pos
    global Marker2Pos
    
    gui.unbind ("<B1-Motion>")
    gui.unbind ("<ButtonRelease-1>")
    if ActiveButton==8:
        xscale=ViewRange/660
        xplace=MarkerLine1.winfo_x()

        Marker1Pos=(xplace-95)*xscale+ViewStart
        print('xplace1:',xplace)
        print('Marker1Pos:',Marker1Pos)
        #updateMarkerPositions()

        taskBtns[0].configure(bg = "red")
    if ActiveButton==9:
        xscale=ViewRange/660
        xplace=MarkerLine2.winfo_x()
        Marker2Pos=(xplace-95)*xscale+ViewStart
        #updateMarkerPositions()
        
        taskBtns[1].configure(bg = "red")
    if ActiveButton==10:
        taskBtns[2].configure(bg = "red")
        UpdateDisplay()
    ActiveButton=-1
    enableButtons(ActiveButton)

def initiateRIGOL():
    global visa_address
    global rm

    if 1:
        #visa_address = 'USB0::0x1AB1::0x0588::DS1EB142204615::INSTR'
        #rm = visa.ResourceManager()
        scope = rm.open_resource(visa_address)
        scope.timeout = 10000 # ms
        scope.encoding = 'latin_1'
        scope.write_termination = None

        #reset scope
        scope.write('*rst')                             
        #start in auto mode
        scope.write(':AUTO')
        #do not display channel 2
        scope.write(':CHAN2:DISP 0')
        #display channel1
        scope.write(':CHAN1:DISP 1')
        #wait 3-4 seconds for the execution
        time.sleep(4.0)

        #get channel status
        if scope.query(':CHAN1:DISP?')=='0':
            print('CHANNEL 1 IS OFF (', scope.query(':CHAN1:DISP?'),')')
        else:
            print('CHANNEL 1 IS ON (', scope.query(':CHAN1:DISP?'),')')
        if scope.query(':CHAN2:DISP?')=='0':
            print('CHANNEL 2 IS OFF (', scope.query(':CHAN2:DISP?'),')')
        else:
            print('CHANNEL 2 IS ON (', scope.query(':CHAN2:DISP?'),')')

        #set time/div to 1 us
        scope.write(':TIMebase:SCALe .000001')
        time.sleep(1.0)
        print('HORIZ. SCALE:',eval(scope.query(':TIMebase:SCALe?')),'seconds')

        #set probe type to 10X
        scope.write(':CHAN1:PROBe 10')
        time.sleep(1.0)
        #set voltage scale
        scope.write(':CHAN1:SCALe 1')
        time.sleep(1.0)
        print('VERT SCALE:',eval(scope.query(':CHANnel1:SCALe?')),'volt/div')
        #set vertical offset
        scope.write(':CHAN1:OFFS 0')
        time.sleep(1.0)

        #set trigger mode
        scope.write(':TRIG:MODE EDGE')
        time.sleep(1.0)
        print('TRIGGER MODE:',scope.query(':TRIG:MODE?'))
        #set trigger source
        scope.write(':TRIG:EDGE:SOUR CHAN1')
        time.sleep(1.0)
        print('TRIGGER SOURCE:',scope.query(':TRIG:EDGE:SOUR?'))
        #set trigger sweep
        scope.write(':TRIG:EDGE:SWE SINGLE')
        time.sleep(1.0)
        print('TRIGGER SWEEP:',scope.query(':TRIG:EDGE:SWE?'))
        #set trigger edge slope
        scope.write(':TRIG:EDGE:SLOP POS')
        time.sleep(1.0)
        print('TRIGGER EDGE:',scope.query(':TRIG:EDGE:SLOP?'))
        #set trigger sensitivity
        scope.write(':TRIG:EDGE:LEV 1.0')
        time.sleep(1.0)
        print('TRIGGER EDGE LEV:',scope.query(':TRIGger:EDGE:LEV?'))
##        #re RUN
##        scope.write(':RUN')
##        while scope.query(':TRIG:STAT?')!="STOP":
##            print('RUNNING')
##        print('STOPPED')

        #scope.write('::WAV:POIN:MODE NORM')
        #scope.write('::WAV:POIN:MODE MAXIMUM')
        time.sleep(1.0)
        print('WAVeform:POINts:MODE:',scope.query(':WAVeform:POINts:MODE?'))
##
##    print('WAVeform:DATA:',scope.query(':WAVeform:DATA?'))
##    a=scope.query(':WAVeform:DATA? CHAN1')
    #exit from remote mode
        scope.write(':KEY:FORCe')

def readRIGOL():
    global visa_address
    global rm

    #visa_address = 'USB0::0x1AB1::0x0588::DS1EB142204615::INSTR'
    #rm = visa.ResourceManager()
    scope = rm.open_resource(visa_address)
    scope.timeout = 10000 # ms
    scope.encoding = 'latin_1'
    scope.write_termination = None



##        #re RUN
##        scope.write(':RUN')
##        while scope.query(':TRIG:STAT?')!="STOP":
##            print('RUNNING')
##        print('STOPPED')

##    scope.write('::WAV:POIN:MODE NORM')
##    time.sleep(1.0)
##    print('WAVeform:POINts:MODE:',scope.query(':WAVeform:POINts:MODE?'))
##
##    print('WAVeform:DATA:',scope.query(':WAVeform:DATA?'))
##    a=scope.query(':WAVeform:DATA? CHAN1')
    #exit from remote mode
   # scope.write(':KEY:FORCe')
   
    pass
def parseLoadedData(lines):
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    
    global PVeloc05Metric
    global PulseWidth
    global Gain
    global ViewRange
    global Marker1Pos
    global Marker2Pos
    global tdrwd

    #messagebox.showinfo("MESSAGE1", str(lines))

    state=0 # before setup section, setup section, trace1 header, trace1 data ...
    #lines were already stripped
    for ix in range(len(lines)):
        line=lines[ix]
        if len(line)==0:
            continue
        if line.count('=')!=0:
            txt_id=line.split('=')[0]
            txt_val=line.split('=')[1]
        else:
            txt_id='none'
            txt_val='none'
            
        if state==0:
            if line[0]==';':
                state=1
                continue
            #nothing required
            continue
#------------------------------------------------------------------------------------                
        if state==1: #if setup state
            if line[0]==';':
                state=2
                continue
            #process lines
            if txt_id=='pulse':
                print(txt_id+'='+txt_val)
                PulseWidth=int(txt_val)
                pwLbl.configure(text=PulseWidths[PulseWidth])
            if txt_id=='gain':
                print(txt_id+'='+txt_val)
                Gain=int(txt_val)
                gainLbl.configure(text='Gain: '+str(Gain))    
            if txt_id=='pveloc/2':
                print(txt_id+'='+txt_val)
                PVeloc05Metric=eval(txt_val)
                pvLbl.configure(text='v/2: '+str(round(PVeloc05Metric,1)) +'m/us')
            if txt_id=='range':
                print(txt_id+'='+txt_val)
                ViewRange=eval(txt_val)
                rangeLbl.configure(text='RANGE: '+str(ViewRange)+'m')
            if txt_id=='viewstart':
                print(txt_id+'='+txt_val)
                ViewStart=eval(txt_val)
            
            if txt_id=='marker1':
                print(txt_id+'='+txt_val)
                Marker1Pos=eval(txt_val)        
            if txt_id=='marker2':
                print(txt_id+'='+txt_val)
                Marker2Pos=eval(txt_val) 
            continue
#------------------------------------------------------------------------------------                
        if state==2: #if trace1 header state
            if line[0]==';':
                state=3
                sample=0
                continue
            #process lines for header
            if txt_id=='state': Trace1Header['state']=int(txt_val)
            elif txt_id=='visible': Trace1Header['visible']=int(txt_val)
            elif txt_id=='tracetype': Trace1Header['tracetype']=int(txt_val)
            elif txt_id=='sampling': Trace1Header['sampling']=float(txt_val)
            elif txt_id=='range': Trace1Header['range']=int(txt_val)
            elif txt_id=='pulse': Trace1Header['pulse']=int(txt_val)
            elif txt_id=='gain': Trace1Header['gain']=int(txt_val)
            elif txt_id=='trigger': Trace1Header['trigger']=int(txt_val)
            elif txt_id=='multiple': Trace1Header['multiple']=int(txt_val)

            continue

        if state==3: #if trace1 data state
            if line[0]==';':
                state=4
                continue
            #process lines for data
            if line.count(',')!=0:
                Signal1Xvals[sample]=float(line.split(',')[0])
                Signal1Yvals[sample]=float(line.split(',')[1])
                sample+=1
            continue
#------------------------------------------------------------------------------------        
        if state==4: #if trace2 header state
            if line[0]==';':
                state=5
                sample=0
                continue
            #process lines for header
            if txt_id=='state': Trace2Header['state']=int(txt_val)
            elif txt_id=='visible': Trace2Header['visible']=int(txt_val)
            elif txt_id=='tracetype': Trace2Header['tracetype']=int(txt_val)
            elif txt_id=='sampling': Trace2Header['sampling']=float(txt_val)
            elif txt_id=='range': Trace2Header['range']=int(txt_val)
            elif txt_id=='pulse': Trace2Header['pulse']=int(txt_val)
            elif txt_id=='gain': Trace2Header['gain']=int(txt_val)
            elif txt_id=='trigger': Trace2Header['trigger']=int(txt_val)
            elif txt_id=='multiple': Trace2Header['multiple']=int(txt_val)
            continue
        if state==5: #if trace2 data state
            if line[0]==';':
                state=6
                continue
            #process lines for data
            if line.count(',')!=0:
                Signal2Xvals[sample]=float(line.split(',')[0])
                Signal2Yvals[sample]=float(line.split(',')[1])
                sample+=1
            continue        
#------------------------------------------------------------------------------------        
        if state==6: #if trace3 header state
            if line[0]==';':
                state=7
                sample=0
                continue
            #process lines for header
            if txt_id=='state': Trace3Header['state']=int(txt_val)
            elif txt_id=='visible': Trace3Header['visible']=int(txt_val)
            elif txt_id=='tracetype': Trace3Header['tracetype']=int(txt_val)
            elif txt_id=='sampling': Trace3Header['sampling']=float(txt_val)
            elif txt_id=='range': Trace3Header['range']=int(txt_val)
            elif txt_id=='pulse': Trace3Header['pulse']=int(txt_val)
            elif txt_id=='gain': Trace3Header['gain']=int(txt_val)
            elif txt_id=='trigger': Trace3Header['trigger']=int(txt_val)
            elif txt_id=='multiple': Trace3Header['multiple']=int(txt_val)
            continue
        if state==7: #if trace3 data state
            if line[0]==';':
                state=8
                continue
            #process lines for data
            if line.count(',')!=0:
                Signal3Xvals[sample]=float(line.split(',')[0])
                Signal3Yvals[sample]=float(line.split(',')[1])
                sample+=1
            continue
        
def saveALLData():
    global Trace1Header
    global Trace2Header
    global Trace3Header
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals
    global ActiveTrace
    
    global PVeloc05Metric
    global PulseWidth
    global Gain
    global ViewRange
    global Marker1Pos
    global Marker2Pos
    global tdrwd

    # ct stores current time
    ct = str(datetime.datetime.now())[0:19]
    ct=ct.replace(':','-')
    ct=ct.replace(' ','-')
    filename=ct+'.tdr.txt'

    
    if TARGETOS=='WINDOWS':
        fulldestpath =os.path.join(os.getcwd(),filename)
    if TARGETOS=='PI':
        #fulldestpath =os.path.join(os.getcwd(),filename)
        fulldestpath =os.path.join(tdrwd,filename)

##        mediadiskpath=''
##        if os.path.exists('/media/pi/WORK'):
##            mediadiskpath='/media/pi/WORK'
##        elif os.path.exists('/media/gd/WORK'):
##            mediadiskpath='/media/gd/WORK'
##
##        print("media found:",mediadiskpath)
##        if len(mediadiskpath)>0:
##            fulldestpath =os.path.join(mediadiskpath,filename)
        
    print('data file path:',fulldestpath)
    with open(fulldestpath, 'w') as wfile:    
        wfile.write('This is a TDR file Ver:000\n')
        
    #first save setup
        txxt=';----------setup\n'
        wfile.write(txxt)
        
        txxt='pulse='+str(PulseWidth)+'\n'
        wfile.write(txxt)
        txxt='gain='+str(Gain)+'\n'
        wfile.write(txxt)
        txxt='pveloc/2='+str(round(PVeloc05Metric,1))+'\n'
        wfile.write(txxt)
        txxt='range='+str(ViewRange)+'\n'
        wfile.write(txxt)
        txxt='viewstart='+str(ViewStart)+'\n'
        wfile.write(txxt)        

        txxt='marker1='+str(round(Marker1Pos,1))+'\n'
        wfile.write(txxt)
        txxt='marker2='+str(round(Marker2Pos,1))+'\n'
        wfile.write(txxt)

        
        SaveTraceHeader(0, wfile)
        SaveSignalData(0, wfile)
        
        SaveTraceHeader(1, wfile)
        SaveSignalData(1, wfile)

        SaveTraceHeader(2, wfile)
        SaveSignalData(2, wfile)

        wfile.close()

def SaveTraceHeader(TraceID, wfile):    
    global Trace1Header
    global Trace2Header
    global Trace3Header

    txxt=';----------trace'+str(TraceID+1)+' header\n'
    wfile.write(txxt)
    
    if TraceID==0:
        traceheader=Trace1Header.copy()
    elif TraceID==1:
        traceheader=Trace2Header.copy()
    else:
        traceheader=Trace3Header.copy()
    
    txxt='state='+str(traceheader['state'])+'\n'
    wfile.write(txxt)
    txxt='visible='+str(traceheader['visible'])+'\n'
    wfile.write(txxt)
    txxt='tracetype='+str(traceheader['tracetype'])+'\n'
    wfile.write(txxt)
    txxt='sampling='+str(traceheader['sampling'])+'\n'
    wfile.write(txxt)
    txxt='range='+str(traceheader['range'])+'\n'
    wfile.write(txxt)
    txxt='pulse='+str(traceheader['pulse'])+'\n'
    wfile.write(txxt)
    txxt='gain='+str(traceheader['gain'])+'\n'
    wfile.write(txxt)
    txxt='trigger='+str(traceheader['trigger'])+'\n'
    wfile.write(txxt)
    txxt='multiple='+str(traceheader['multiple'])+'\n'

def SaveSignalData(TraceID, wfile):    
    global Signal1Xvals
    global Signal1Yvals
    global Signal2Xvals
    global Signal2Yvals
    global Signal3Xvals
    global Signal3Yvals

    if TraceID==0:
        signalX=Signal1Xvals[ : ]
        signalY=Signal1Yvals[ : ]          
    elif TraceID==1:
        signalX=Signal2Xvals[ : ]
        signalY=Signal2Yvals[ : ]    
    else:
        signalX=Signal3Xvals[ : ]
        signalY=Signal3Yvals[ : ]    
        
    txxt=';----------trace'+str(TraceID+1)+' signal\n'
    wfile.write(txxt)
    for i in range(len(signalY)):
        veri = (signalX[i])           
        wfile.write(f'{veri:.12f}' + ',')
        veri = (signalY[i])
        wfile.write(f'{veri:f}' + '\n')
            
def writeCurrentSetup():
    global PVeloc05Metric
    global PulseWidth
    global Gain
    global ViewRange
    global ViewStart
    global Marker1Pos
    global Marker2Pos
    global tdrwd

    if TARGETOS=='WINDOWS':
        fulldestpath =os.path.join(tdrwd,'setup.txt')
    if TARGETOS=='PI':
        #fulldestpath =os.path.join(os.getcwd(),'setup.txt')
        fulldestpath =os.path.join(tdrwd,'setup.txt')
    with open(fulldestpath, 'w') as wfile:    
        wfile.write('This is a setup file\n')

        txxt='pulse='+str(PulseWidth)+'\n'
        wfile.write(txxt)
        txxt='gain='+str(Gain)+'\n'
        wfile.write(txxt)
        txxt='pveloc/2='+str(round(PVeloc05Metric,1))+'\n'
        wfile.write(txxt)
        txxt='range='+str(ViewRange)+'\n'
        wfile.write(txxt)
        txxt='viewstart='+str(ViewStart)+'\n'
        wfile.write(txxt)        

        txxt='marker1='+str(round(Marker1Pos,1))+'\n'
        wfile.write(txxt)
        txxt='marker2='+str(round(Marker2Pos,1))+'\n'
        wfile.write(txxt)
        
        wfile.close()
            
def readCurrentSetup():
    global PVeloc05Metric
    global PulseWidth
    global Gain
    global ViewRange
    global ViewStart
    global Marker1Pos
    global MarkerLine1
    global Marker2Pos
    global MarkerLine2
    global tdrwd

    fullsetuppath =os.path.join(tdrwd,'setup.txt')

    if not os.path.exists(fullsetuppath):
        print("setup file doesn't exist")
        return
    
    f = open(fullsetuppath, "r")
    setuplines = f.readlines()
    f.close()
    len_ = len(setuplines)

    for i in range(0, len_):
        eachline=setuplines[i]
        if eachline[-1]=='\n':
            eachline=eachline[:-1]

        if eachline.count('=')!=0:
            txt_id=eachline.split('=')[0]
            txt_val=eachline.split('=')[1]
        else:
            txt_id='none'
            txt_val='none'

        if txt_id=='pulse':
            print(txt_id+'='+txt_val)
            PulseWidth=int(txt_val)
            pwLbl.configure(text=PulseWidths[PulseWidth])
        if txt_id=='gain':
            print(txt_id+'='+txt_val)
            Gain=int(txt_val)
            gainLbl.configure(text='Gain: '+str(Gain))    
        if txt_id=='pveloc/2':
            print(txt_id+'='+txt_val)
            PVeloc05Metric=eval(txt_val)
            pvLbl.configure(text='v/2: '+str(round(PVeloc05Metric,1)) +'m/us')
        if txt_id=='range':
            print(txt_id+'='+txt_val)
            ViewRange=eval(txt_val)
            rangeLbl.configure(text='RANGE: '+str(ViewRange)+'m')
        if txt_id=='viewstart':
            print(txt_id+'='+txt_val)
            ViewStart=eval(txt_val)
        
        if txt_id=='marker1':
            print(txt_id+'='+txt_val)
            Marker1Pos=eval(txt_val)        
        if txt_id=='marker2':
            print(txt_id+'='+txt_val)
            Marker2Pos=eval(txt_val)

def doOnClosingMaster():
    plt.close()
    gui.destroy()

#----------------------------------------------------------------------------------
gui = Tk(className=' TDR-GD R1.2')
gui.configure(background="blue")
gui.protocol('WM_DELETE_WINDOW', doOnClosingMaster) 

#gui.state('zoomed')
if TARGETOS=='PI':
    # pencere boyunu kur
    gui.geometry("1024x600")   
    #gui.wm_attributes('-type', 'splash')
    gui.wm_attributes('-fullscreen','false')
else:
    # pencere boyunu kur
##    gui.state('zoomed')
##    gui.update()
##    print(len(screeninfo.get_monitors()))
##    screen_width=gui.winfo_screenwidth()  #gui.winfo_screenwidth()
##    print('screen width=',screen_width)
    
#    [Monitor(x=0, y=0, width=1920, height=1080, width_mm=344, height_mm=194, name='\\\\.\\DISPLAY1', is_primary=True),
#            Monitor(x=1920, y=0, width=2560, height=1080, width_mm=798, height_mm=334, name='\\\\.\\DISPLAY4', is_primary=False)]
  
    if len(screeninfo.get_monitors())>1:
        gui.geometry('%dx%d+%d+%d' % (1024, 630, 3400, 10))
        gui.update()
        screen_width=gui.winfo_screenwidth()  #gui.winfo_screenwidth()
        print('screen width=',screen_width)
    else:
        gui.geometry("1024x630")    #'+%d+%d'%(x,y)
    gui.resizable(False, False) 
displayW=1024

ActiveButton=-1
ActiveMenu=0
ActiveTask=0
#place frames
frameBtn1= Button(gui)
frameBtn1.place (x=10, y=490, width=displayW-20, height=90)
frameBtn1.configure(bg = "blue",  state=DISABLED)

frameBtn2= Button(gui)
frameBtn2.place (x=840, y=100, width=174, height=380)
frameBtn2.configure(bg = "blue",  state=DISABLED)

   
#place labels
TitleLbl= Label(gui, text="TDR VER.1.3a", font="Helvetica 18 bold")
TitleLbl.place(x = 0, y = 0, width = 1024, height = 40)
TitleLbl.configure(bg = "blue", fg="white")

rangeLbl= Label(gui, text="RANGE: 100m", font="Helvetica 14")
rangeLbl.place(x = 10, y = 45, width = 150, height = 40)
rangeLbl.configure(bg = "white", fg="black")

dstLbl= Label(gui, text="DIST: 100m", font="Helvetica 14")
dstLbl.place(x = 170, y = 45, width = 150, height = 40)
dstLbl.configure(bg = "white", fg="black")

pvLbl= Label(gui, text="v/2: 100m/us", font="Helvetica 14")
pvLbl.place(x = 330, y = 45, width = 150, height = 40)
pvLbl.configure(bg = "white", fg="black")

pwLbl= Label(gui, text="Pulse:50ns", font="Helvetica 14")
pwLbl.place(x = 490, y = 45, width = 150, height = 40)
pwLbl.configure(bg = "white", fg="black")

gainLbl= Label(gui, text="Gain: 5", font="Helvetica 14")
gainLbl.place(x = 650, y = 45, width = 150, height = 40)
gainLbl.configure(bg = "white", fg="black")

CheckBoxsamplesVar = IntVar()
CheckBoxsamplesVar.set(0) 
CheckBoxsamples = Checkbutton(gui, text='show samples',variable=CheckBoxsamplesVar,  \
                            command=lambda:UpdateDisplay())
                                                #onvalue=1, offvalue=0,
CheckBoxsamples.place(x=840-30, y=10,w=100, h=20)

#place trace buttons
trcBtns=[0,1,2]
trcBtns[0]= Button(gui, text="1\nSNGL",  font="Helvetica 10 bold", command = lambda:selectTrcFunction(0))
trcBtns[0].place(x = 840-30, y =40, width = 60, height = 50)
trcBtns[0].configure(bg = "yellow", fg="black")
#trc1Btn["state"]=NORMAL

trcBtns[1]= Button(gui, text="2\nEMPTY", font="Helvetica 10 bold", command = lambda:selectTrcFunction(1))
trcBtns[1].place(x = 900-20, y =40, width = 60, height = 50)
trcBtns[1].configure(bg = "gray", fg="black")

trcBtns[2]= Button(gui, text="3\nEMPTY", font="Helvetica 10 bold", command = lambda:selectTrcFunction(2))
trcBtns[2].place(x =960-10, y =40, width =60 , height =50)
trcBtns[2].configure(bg = "gray", fg="black")

Btnwidth=160
Btnheight= 70

#place menu buttons
menuBtns=[0,1,2,3,4]
x1=848
y1=105
menuBtns[0]= Button(gui, text=" VIEW \n MENU ", font="Helvetica 16 bold", command = lambda:selectMenuFunction(0))
menuBtns[0].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
menuBtns[0].configure(bg = "yellow", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

y1+=75
menuBtns[1]= Button(gui, text=" MEASURE \n MENU ", font="Helvetica 16 bold", command = lambda:selectMenuFunction(1))
menuBtns[1].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
menuBtns[1].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

y1+=75
menuBtns[2]= Button(gui, text=" CAPTURE \n MENU ", font="Helvetica 16 bold", command = lambda:selectMenuFunction(2))
menuBtns[2].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
menuBtns[2].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

y1+=75
menuBtns[3]= Button(gui, text=" FILE \n MENU ", font="Helvetica 16 bold", command = lambda:selectMenuFunction(3))
menuBtns[3].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
menuBtns[3].configure(bg = "red", fg="black")
menuBtns[3].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

y1+=75
menuBtns[4]= Button(gui, text=" SETUP ", font="Helvetica 16 bold", command = lambda:selectMenuFunction(4))
menuBtns[4].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
menuBtns[4].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

# place task buttons
taskBtns=[0,1,2,3,4,5]
y1=500
x1=18
x2=(1024-20-8)/6 

taskBtns[0]= Button(gui, text="RANGE \n-", font="Helvetica 16 bold", command = lambda:selectTaskFunction(0))
taskBtns[0].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[0].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

x1=x1+x2
taskBtns[1]= Button(gui, text="RANGE \n+", font="Helvetica 16 bold", command = lambda:selectTaskFunction(1))
taskBtns[1].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[1].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

x1=x1+x2
taskBtns[2]= Button(gui, text="SHIFT \n-", font="Helvetica 16 bold", command = lambda:selectTaskFunction(2))
taskBtns[2].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[2].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

x1=x1+x2
taskBtns[3]= Button(gui, text="SHIFT \n+", font="Helvetica 16 bold", command = lambda:selectTaskFunction(3))
taskBtns[3].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[3].configure(bg = "red", fg="black",activebackground='red',borderwidth=5,highlightthickness=0)

x1=x1+x2
taskBtns[4]= Button(gui, text="---", font="Helvetica 16 bold", command = lambda:selectTaskFunction(4))
taskBtns[4].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[4].configure(bg = "red", fg="black")
taskBtns[4].configure(state=DISABLED, text='', bg = "blue", fg="blue", activebackground='red',borderwidth=5,highlightthickness=0)

x1=x1+x2
taskBtns[5]= Button(gui, text="---", font="Helvetica 16 bold", command = lambda:selectTaskFunction(5))
taskBtns[5].place(x = x1, y = y1, width = Btnwidth, height = Btnheight)
taskBtns[5].configure(bg = "red", fg="black")
taskBtns[5].configure(state=DISABLED, text='', bg = "blue", fg="blue", activebackground='red',borderwidth=5,highlightthickness=0)

readCurrentSetup()  

#draw initial figure here
fig = plt.figure()
newdpi=fig.dpi
##fig.set_size_inches(640/newdpi,480/newdpi)
ax = fig.add_subplot(111)

ax.set_title("TITLE")
ax.set_xlabel("X AXIS\n")
ax.set_ylabel("Y AXIS")
ax.set_xlim(0, 100)
ax.set_ylim(0, 255)
ax.grid( which='major', color='#666666', linestyle='-')
ax.minorticks_on()
ax.grid( which='minor', color='#666666', linestyle='-', alpha=0.4)

mycanvas2= Canvas(gui, bg = "white", width=820, height=380)
mycanvas2.config(highlightthickness=0)
mycanvas2.place (x=10, y=100)
mycanvas2.update
##UpdateDisplay()

mycanvas = Canvas(mycanvas2)
#mycanvas.place(x=410, y=182, width=900, height=390, anchor=CENTER) #370
mycanvas.place(x=-20, y=0, width=850, height=370) #370
mycanvas.update
canvas = FigureCanvasTkAgg(fig, master=mycanvas)
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

#toolbar = NavigationToolbar2Tk(canvas, root)
toolbar = NavigationToolbar2Tk(canvas, gui)
toolbar.update()

plt.draw()
fig.canvas.flush_events()

MarkerLine1= Label(gui, text="")
MarkerLine1.place(x = 200, y = 160, width = 2, height = 256)
##MarkerLine1.configure(bg = "magenta", fg="magenta")
MarkerLine1.configure(bg = "brown")

MarkerLine2= Label(gui, text="")
MarkerLine2.place(x = 400, y = 160, width = 2, height = 256)
##MarkerLine2.configure(bg = "cyan", fg="cyan")
MarkerLine2.configure(bg = "brown")

updateMarkerPositions()
gui.update()
dstLbl.configure(text='DIST: '+str(round((MarkerLine2.winfo_rootx()-MarkerLine1.winfo_rootx() )*ViewRange/(766-106),1))+'m')

UpdateDisplay()

DetectConnectedDevices()

gui.mainloop()
