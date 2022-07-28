#see https://docs.python.org/3/library/socket.html for documentation on python socket library

#The purpose of this script is to demonstrate the correct order of operations
# for using SCPI commands to get reliable measurements from the Bird pulse sensor via ethernet bridge

#The sequency of operations in this script follow those outlined by the block diagram in the Recommended Procedure for 
# Pulse Sensor Measurements document which should be included in this package

from logging.config import listen
import time
import socket

#Creates a socket connection between the computer and ethernet bridge
#Connects computer to the bridge's IP address via port 5025 
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = input('Enter the IP address of the ethernet bridge (or press ENTER to set IP address to the default): ')
if IP == '':
    sock.connect(('192.168.1.151', 5025)) #default IP address
else:
    sock.connect((IP, 5025))

#Encodes user's SCPI command so it can be sent to the ethernet bridge
def sendSCPIcommand(msg):
    msg = str(msg) + '\n'
    msg = msg.encode()
    sock.send(msg) #sends the command to the ethernet bridge

#Note: this method only makes sense to call if a query has been sent
#Tells the computer to listen for an answer after a query is sent to the ethernet bridge.
def readResponse():
    resp = sock.recv(1024)#1024 should be a large enough byte size for this script, but can be changed if needed
    return resp.decode()

#Asks the user if they would like to specify a frequency for the sensor to track or leave it in auto-tracking
#If the exact frequency of the line is known, then it should be entered in MHz
#Otherwise, auto-tracking should be selected
def measureFrequency():
    measureMode = input('Do you want to specify a frequency to track or perform auto-tracking? (freq/auto): ')
    measureMode = measureMode.lower()
    if measureMode == 'freq':
        freq = input('enter frequecny in MHz: ')
        sendSCPIcommand('SENS:FREQ ' + str(freq))
    elif measureMode == 'auto':
        return
    else:
        print('invalid input')
        measureFrequency()

#Corresponds to the *STB? query and what to do depending on the answer.
#*STB? reads the status byte
#See Recommended Procedure for Pulse Sensor Measurements document for important bits and more details
def readStatusByte():
    sendSCPIcommand('*STB?')
    ans = int(readResponse())
    if ans & (1 << 2):
        sendSCPIcommand('SYST:ERR?')
        errorNumber = int(readResponse().split(',')[0])
        while errorNumber > 0:
            sendSCPIcommand('SYST:ERR?')
            errorNumber = int(readResponse().split(',')[0])
    elif ans & (1 << 3):
        sendSCPIcommand('STAT:QUES:COND?')
        questionableCondition = int(readResponse())
        if questionableCondition & (1 << 3):
            print('Note: Calibration not valid at measured frequency\n')
        elif questionableCondition & (1 << 5):
            print('Note: Insufficient RF amplitude or duration to measure frequency\n') 
        elif questionableCondition & (1 << 8):
            print('Note: Calibration not valid\n')

#Tells the sensor to read and display either forward ('f') or reflected ('r') power depending on the user's request
def readPower(powerMeas):
    if powerMeas == 'f' or powerMeas == 'F':
        sendSCPIcommand('FETC:FORW:AVER?')
        answer = readResponse()
        print(answer.strip() + ' Watts')
    elif powerMeas == 'r' or powerMeas == 'R':
        sendSCPIcommand('FETC:REFL:AVER?')
        answer = readResponse()
        print(answer.strip() + ' Watts')
    else:
        powerMeas = input('Invalid entry. Please enter ''f'' for forward power or ''r'' for reflected: ')
        readPower(powerMeas)


#This is where the recommended sequence of SCPI commands begins
#Sequence corresponds to the Recommended Procedure for Pulse Sensor Measurements flow chart
sendSCPIcommand('*RST')

time.sleep(0.5) #wait 500ms before continuing

measureFrequency()
while True:
    sendSCPIcommand('*CLS')
    
    time.sleep(0.5) #wait 500ms before continuing

    sendSCPIcommand('INIT') 

    sendSCPIcommand('*OPC?')
    readResponse() #prevents further operations until all pending operations have occurred

    readStatusByte() #handles the sequence beginning with the command *STB?

    powerMeas = input('Read Forward Average Power or Relfected Average Power? (f/r): ')
    if powerMeas == 'exit':
        break
    readPower(powerMeas)