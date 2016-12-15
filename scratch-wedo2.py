#!/usr/bin/env python

import sys
import random
import traceback
import logging
import binascii

from gattlib import GATTRequester
from time import sleep
from struct import pack, unpack
from flask import Flask

HANDLE_PORT = 0x15
HANDLE_BUTTON = 0x11
HANDLE_SENSOR_VALUE = 0x32
HANDLE_INPUT_COMMAND = 0x3a
HANDLE_OUTPUT_COMMAND = 0x3d

HANDLE_CCC_BUTTON = 0x12
HANDLE_CCC_PORT = 0x16
HANDLE_CCC_SENSOR_VALUE = 0x33

TYPE_MOTOR = 0x1
TYPE_RGB_LIGHT = 0x17
TYPE_TILT = 0x22
TYPE_MOTION = 0x23

COMMAND_ID_INPUT_VALUE = 0
COMMAND_ID_INPUT_FORMAT = 1
COMMAND_TYPE_READ = 1
COMMAND_TYPE_WRITE = 2

INPUT_FORMAT_UNIT_RAW = 0
INPUT_FORMAT_UNIT_PERCENT = 1
INPUT_FORMAT_UNIT_SI = 2

TILT_SENSOR_MODE_TILT = 1

TILT_NEUTRAL = 0
TILT_BACKWARD = 3 
TILT_RIGHT = 5
TILT_LEFT = 7
TILT_FORWARD = 9
TILT_UNKNOWN = 10

class Requester(GATTRequester):
    def __init__(self, address, connect = True):
        super(Requester, self).__init__(address, connect)

        self.motor = 0        
        self.sensor = [0] * 7
        self.button = 0
        self.direction = 0
        self.distance = 0

    def on_notification(self, handle, data):

        data = data[3:]
        
        if handle == HANDLE_PORT:
            port, attach = unpack("<BB", data[0:2])            
            if attach: 
                print("Notification on handle: {} {} {}".format(handle, len(data), binascii.hexlify(data)))

                hubIndex, type = unpack("<BB", data[2:4])
                self.sensor[port] = type

                if type == TYPE_TILT:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_TILT, TILT_SENSOR_MODE_TILT, 1, INPUT_FORMAT_UNIT_RAW, 1))
                elif type == TYPE_MOTION:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_MOTION, 0, 1, INPUT_FORMAT_UNIT_RAW, 1))
                elif type == TYPE_MOTOR:
                    self.motor = port

        elif handle == HANDLE_SENSOR_VALUE:
            revision, port = unpack("<BB", data[0:2])
            if self.sensor[port] == TYPE_TILT:            
              self.direction = unpack("<B", data[2:])[0]
            elif self.sensor[port] == TYPE_MOTION:
              self.distance = unpack("<B", data[2:])[0]              
        elif handle == HANDLE_BUTTON:
            self.button = unpack("<B", data[0])[0]
        else:
            print("Notification on handle: {} {} {}".format(handle, len(data), binascii.hexlify(data)))

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

ADDRESS = sys.argv[1]

motorPower = {}
busy = {}

req = Requester(ADDRESS, False)

req.connect(True)

req.write_without_response_by_handle(HANDLE_CCC_BUTTON, pack("<h", 0x0001))
req.write_without_response_by_handle(HANDLE_CCC_PORT, pack("<h", 0x0001))
req.write_without_response_by_handle(HANDLE_CCC_SENSOR_VALUE, pack("<h", 0x0001))

@app.route("/crossdomain.xml")
def crossdomain():
    return '''
        <cross-domain-policy>
          <allow-access-from domain="*" to-ports="<yourPort>"/>
        </cross-domain-policy>
    '''

@app.route("/reset_all")
def reset():
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, "\x06\x04\x01\x00")
    return ""

@app.route("/setLight/<color>")
def setLight(color):
    COLORS = ( "off", "pink", "purple", "blue", "sky blue", "teal", "green", "yellow", "orange", "red", "white")

    if color == "random":
      color = random.randint(1,10)
    else:
      color = COLORS.index(color)

    print("Set light color to " + str(color))
    
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, "\x06\x04\x01" + chr(color))
    return ""

@app.route("/setMotorDirection/<motor>/<direction>")
def setMotorDirection(motor, direction):
    DIRECTION = ["that way", "other way", "this way"]
    try:
        motorDirection[motor] = DIRECTION.index(direction) - 1
    except Exception as e:
      logging.error(traceback.format_exc())
    
    print("Set motor direction of " + motor + " to " + direction)

    return ""
 
@app.route("/startMotorPower/<motor>/<power>")
def startMotorPower(motor, power):
    try:
        motorPower[motor] = int(power)
    except Exception as e:
      logging.error(traceback.format_exc())
    
    print("Set motor power of " + motor + " to " + power)

    return ""

@app.route("/motorOn/<motor>")
def motorOn(motor):
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbb", req.motor, 0x01, 0x01, motorDirection.get(motor, 1) * motorPower.get(motor, 50)))    
    
    return ""

@app.route("/motorOff/<motor>")
def motorOff(motor):
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbb", req.motor, 0x01, 0x01, 0x00))

    return ""

@app.route("/motorOnFor/<id>/<motor>/<duration>")
def motorOnFor(id, motor, duration):
    busy[id] = True
    #print("Start " + motorPower.get(motor, 50) + " " + duration)
    print "motor " + str(req.motor)
    motorOn(motor)
    sleep(float(duration))
    del busy[id]
    print "Stop"
    
    motorOff(motor)
    return ""

@app.route("/poll")
def poll():
    BUTTON_STR = ('false', 'true')
    TILT_STR = ( "any", "any", "any", "up", "any", "right", "any", "left", "any", "down", "any" )

    result = []
    result.append("button1 " + BUTTON_STR[req.button])
    result.append("tilt " + TILT_STR[req.direction])
    result.append("distance " + str(req.distance))
    for id in busy:
      result.append("_busy " + id)
    return "\n".join(result)

@app.errorhandler(Exception)
def all_exception_handler(error):
   logging.error(traceback.format_exc())
   return 'Error', 500

if __name__ == "__main__":
    app.run(port=17311, threaded=True)
