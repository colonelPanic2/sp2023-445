# NOTE: This file is just for reference. It is not used in the
# actual code

import RPi.GPIO as io
import time

#GPIO Mode (BOARD / BCM)
io.setmode(io.BCM)

#set GPIO Pins
GPIO_TRIGGER = 18
GPIO_ECHO = 24

#set GPIO direction (IN / OUT)
io.setup(GPIO_TRIGGER, io.OUT)
io.setup(GPIO_ECHO, io.IN)

def distance():
    # set Trigger to HIGH
    io.output(GPIO_TRIGGER, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    io.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while io.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while io.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance

if __name__ == '__main__':
    try:
        while True:
            dist = distance()
            print ("Measured Distance = %.1f cm" % dist)    
            time.sleep(1)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        io.cleanup()