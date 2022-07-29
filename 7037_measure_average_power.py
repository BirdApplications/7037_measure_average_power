#see https://docs.python.org/3/library/socket.html for documentation on python socket library

#The purpose of this script is to demonstrate the correct order of operations
# for using SCPI commands to get reliable measurements from the Bird pulse sensor via ethernet bridge

#The sequency of operations in this script follow those outlined by the block diagram in the Recommended Procedure for 
# Pulse Sensor Measurements document which should be included in this package

from threading import main_thread
import time
import socket

from pip import main

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

if __name__ == ‘__main__’:

    #Creates a socket connection between the computer and ethernet bridge
    #Connects computer to the bridge's IP address via port 5025 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    IP = input('Enter the IP address of the ethernet bridge (or press ENTER to set IP address to the default): ')
    if IP == '':
        sock.connect(('192.168.1.151', 5025)) #default IP address
    else:
        sock.connect((IP, 5025))

    #This is where the recommended sequence of SCPI commands begins
    #Sequence corresponds to the Recommended Procedure for Pulse Sensor Measurements flow chart

    sendSCPIcommand('*RST') #Resturn the sensor to its default configuration settings

    time.sleep(0.5) #wait 500ms before continuing

    sendSCPIcommand('*CLS')

    while True:
        
        time.sleep(0.5) #wait 500ms before continuing

        sendSCPIcommand('INIT') 

        sendSCPIcommand('*OPC?')
        readResponse() #prevents further operations until all pending operations have occurred

        readStatusByte() #handles the sequence beginning with the command *STB?

        print('Type EXIT to end the program')
        powerMeas = input('Press ENTER to make a measurement:')

        if powerMeas.lower() == 'exit':
            break
        else:
            sendSCPIcommand('FETC:AVER?')
            answer = readResponse()
            print(answer.strip() + ' Watts')