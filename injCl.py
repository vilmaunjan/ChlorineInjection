import RPi.GPIO as GPIO
import time

GPIO.setmode( GPIO.BOARD )

timeBeforePumpOn = 5 # time before granular tank pump turns on
timeBeforeV2OrV3Opens = 5 # time between V4 opens and (V3 or V2) open
flushTime = 7   # time needed for initial flushing

onDC = 5.0
offDC = 14.0

servoHertz = 100

dutyToDegree = ( offDC - onDC ) / 90 # range at 50Hz for 90 degrees (14.0ms - 5.0ms)

curV1Pos = offDC
curV2Pos = offDC
curV3Pos = offDC
curV4Pos = offDC
curV5Pos = offDC

# initialize LED pin #'s
granPumpLED = 29
mainPumpLED = 31
orpSensorLED = 33

servoV1 = 18    # Valve 1 pin # 
servoV2 = 15    # Valve 2 pin #
servoV3 = 16    # Valve 3 pin #
servoV4 = 13    # Valve 4 pin #
servoV5 = 11    # Valve 5 pin #

# initializing LED pins as output
GPIO.setup( granPumpLED, GPIO.OUT )
GPIO.setup( mainPumpLED, GPIO.OUT )
GPIO.setup( orpSensorLED, GPIO.OUT )

# initialize the servo pins as output pins
GPIO.setup( servoV1, GPIO.OUT )
GPIO.setup( servoV2, GPIO.OUT )
GPIO.setup( servoV3, GPIO.OUT )
GPIO.setup( servoV4, GPIO.OUT )
GPIO.setup( servoV5, GPIO.OUT )

# initialize PWM servo and Hz value
V1 = GPIO.PWM( servoV1, servoHertz )    
V2 = GPIO.PWM( servoV2, servoHertz )
V3 = GPIO.PWM( servoV3, servoHertz )
V4 = GPIO.PWM( servoV4, servoHertz )
V5 = GPIO.PWM( servoV5, servoHertz )

def duty(angle):
    tempDuty = float( angle ) / 10.0 + 5

def selectChlorineType(valve, typeCl, currentPos):
    for i in range (90):
        if typeCl == "1":
            currentPos -= dutyToDegree
        elif typeCl == "2":
            currentPos += dutyToDegree
        valve.ChangeDutyCycle(currentPos)
        time.sleep(.01)
    return currentPos

def wideOpen(valve):
    tempDC = offDC
    for i in range (90):
        tempDC -= dutyToDegree
        valve.ChangeDutyCycle(tempDC)
        time.sleep(.01)
    return tempDC

def turnTo(valve, angle):
    # ISSUE ONLY GOES UP CURRENTLY 
	# TODO
    tempDC = offDC
    for i in range (angle):
        tempDC -= dutyToDegree
        valve.ChangeDutyCycle(tempDC)
        time.sleep(.01)
    return tempDC

def shutAll(valve, currentPos):
    if currentPos < offDC:
        currentPos += dutyToDegree
        valve.ChangeDutyCycle(currentPos)
    elif currentPos > offDC:
        currentPos -= dutyToDegree
        valve.ChangeDutyCycle(currentPos)

    time.sleep(.001)
    return currentPos


def sense(valve3, currentPos3, valve4, currentPos4):
     desiredConcentration = 600
     initialConcentration = str(input("Type concentration: "))

     ic = int(initialConcentration)
     GPIO.output(orpSensorLED, GPIO.HIGH)
     print "sensing"
     time.sleep(1)

     conDif = desiredConcentration - ic  # concentration difference
     if conDif > 0:
        currentPos3 += dutyToDegree
        currentPos4 -= dutyToDegree
        valve3.ChangeDutyCycle(currentPos3)
        valve4.ChangeDutyCycle(currentPos4)

     elif conDif < 0:
        valve3 -= dutyToDegree
        valve4 += dutyToDegree
        valve3.ChangeDutyCycle(currentPos3)
        valve4.ChangeDutyCycle(currentPos4)

     GPIO.output(orpSensorLED, GPIO.LOW)
     time.sleep(1)

     return currentPos3, currentPos4

def flushing():
    concentration = 500
    while (concentration >100):
        # Valve open loop
        for i in range(90):
            curV1Pos = selectChlorineType(V1, typeCl, curV1Pos)
            curV2Pos = wideOpen(V2, curV2Pos)
            curV3Pos = wideOpen(V3, curV3Pos)
            curV4Pos = wideOpen(V4, curV4Pos)
            curV5Pos = wideOpen(V5, curV5Pos)
            time.sleep(.01)

        #Turn off sensor in tank 3 and pump 1
        GPIO.output(granPumpLED, GPIO.LOW)
        GPIO.output(orpSensorLED, GPIO.LOW)

        str(raw_input("Disconnect lines and hit enter"))
        print "Closing V1, V4, and V5"
        for i in range(90):
            curV1Pos = shutAll(V1, curV1Pos)
            curV4Pos = shutAll(V4, curV4Pos)
            curV5Pos = shutAll(V5, curV5Pos)
            time.sleep(.01)
        time.sleep(5) #time delay to empty the tanks
        GPIO.output(mainPumpLED, GPIO.LOW) #turn off main pump before V2/V3 so that pump doesnt get damaged
        for i in range(90):
            curV1Pos = shutAll(V2, curV2Pos)
            curV4Pos = shutAll(V3, curV3Pos)


    
def killLEDs():
    GPIO.output(granPumpLED, GPIO.LOW)
    GPIO.output(mainPumpLED, GPIO.LOW)
    GPIO.output(orpSensorLED, GPIO.LOW)

try:
    ''' initialize all LED's to off '''
    killLEDs()
    
    ''' Close all valves '''
    V1.start( offDC )
    V2.start( offDC )
    V3.start( offDC )
    V4.start( offDC )
    V5.start( offDC )
    
    ''' Select valve now so user can walk away for the intial flush '''
    while(True):
        try:
            typeCl = str(input( "Tank: " ))
            temp = int(typeCl)
            if temp > 0 and temp < 3:
                if typeCl == "1":
                    V3.stop()
                    print "V3 Disabled"
                else:
                    V2.stop()
                    print "V2 Disabled"
                break
            else:
                continue
        except:
            continue

    ''' User presses enter to continue after hooking up lines '''
    start = str(raw_input("Connect lines and hit enter"))
    
    ''' Open V5 '''
    curV5Pos = wideOpen(V5)
    #print curV5Pos

    print "Flushing new line\n"
    time.sleep(flushTime) # alloted time used for initial flushing
    print "Flush finished"
    time.sleep(1)

    ''' Open V1 to respective chlorine tank (Liquid T1 or Granular T2) '''
    curV1Pos = selectChlorineType(V1, typeCl, curV1Pos)

    print "Chlorine tank filling"
    time.sleep(timeBeforePumpOn)
    if typeCl == "2":
        # turn on LED for pump 1
        GPIO.output(granPumpLED, GPIO.HIGH)
        print "Granular pump on"
    time.sleep(2)

    ''' Open V4 '''
    curV4Pos = turnTo(V4, 67)	# try .75(offDC - onDC) for 3/4 the way open
    
    ''' delay for T3 better dilution '''
    print "Mixing tank filling with water"
    time.sleep(timeBeforeV2OrV3Opens)
    
    ''' Open V3 or V2'''
    if typeCl == "1":
        curV2Pos = turnTo(V2, 67)
    elif typeCl == "2":
        curV3Pos = turnTo(V3, 67)

    ''' LOOP till 600ppm && tank is 3/4 filled '''
    # TODO
    volume = 20 #assuming this is the time that takes to fill 3/4 of the tank
    while (volume > 0):
        curV3Pos,curV4Pos = sense(V3,curV3Pos,V4,curV4Pos)
        volume-=1

    ''' Setup Completed '''
    
    ''' Turn T3 pump on '''
    # turn pump 2 LED on
    GPIO.output(mainPumpLED, GPIO.HIGH)
    print "Pumping solution to new line"
    
    ''' LOOP to maintain 600ppm && 3/4 fill mark '''
    # TODO
    
    while True:
        exit = input("<Enter> to quit loop: ")  # if user press e, exit loop
        if exit == "e":
            break
        else:
            curV3Pos, curV4Pos = sense(V3, curV3Pos, V4, curV4Pos)
    print("Finishing chlorination process..")

    print("Starting flushing process..")
    flushing()

    killLEDs()
    ''' close all valves '''
    # Close all valves
    for i in range (90):
        curV1Pos = shutAll(V1, curV1Pos)
        curV2Pos = shutAll(V2, curV2Pos)
        curV3Pos = shutAll(V3, curV3Pos)
        curV4Pos = shutAll(V4, curV4Pos)
        curV5Pos = shutAll(V5, curV5Pos)
      
    V1.stop()
    V2.stop()
    V3.stop()
    V4.stop()
    V5.stop()  # relax the motor
    GPIO.cleanup() 
except:
    print "Failed"
    V1.stop()
    V2.stop()
    V3.stop()
    V4.stop()
    V5.stop()  # relax the motor
    GPIO.cleanup()  # cleanup used GPIO signals
