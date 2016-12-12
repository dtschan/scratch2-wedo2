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
HANDLE_SENSOR_VALUE = 0x32
HANDLE_INPUT_COMMAND = 0x3a
HANDLE_OUTPUT_COMMAND = 0x3d

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

class Requester(GATTRequester):
    def __init__(self, address, connect = True):
        super(Requester, self).__init__(address, connect)

        self.direction = 0

    def on_notification(self, handle, data):

        data = data[3:]
        
        if handle == HANDLE_PORT:
            port, attach = unpack("<BB", data[0:2])
            if attach: 
                hubIndex, type = unpack("<BB", data[2:4])
                print "port " + str(port) + " " + str(attach)
            
                if type == TYPE_TILT:
                    print req.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_TILT, TILT_SENSOR_MODE_TILT, 1, INPUT_FORMAT_UNIT_RAW, 1))
                elif type == TYPE_MOTION:
                    print req.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_MOTION, 0, 1, INPUT_FORMAT_UNIT_SI, 1))

        elif handle == HANDLE_SENSOR_VALUE:
            revision, port = unpack("<BB", data[0:2])
            self.direction = unpack("<B", data[2:])[0]
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

req.write_without_response_by_handle(0x0037, pack("<h", 0x0001))
req.write_without_response_by_handle(0x0033, pack("<h", 0x0001))
req.write_without_response_by_handle(0x0012, pack("<h", 0x0001))
req.write_without_response_by_handle(0x0016, pack("<h", 0x0001))

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

@app.route("/startMotorPower/<motor>/<power>")
def startMotorPower(motor, power):
    try:
        motorPower[motor] = power
    except Exception as e:
      logging.error(traceback.format_exc())
    
    print("Set motor power of " + motor + " to " + power)

    return ""
 
@app.route("/motorOnFor/<id>/<motor>/<duration>")
def motorOnFor(id, motor, duration):
    busy[id] = True
    print("Start " + motorPower.get(motor, 50) + " " + duration)
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbb", 0x01, 0x01, 0x01, int(motorPower.get(motor, 50))))
    sleep(float(duration))
    del busy[id]
    print "Stop"
    
    req.write_by_handle(HANDLE_OUTPUT_COMMAND, "\x01\x01\x01\x00")
    return ""

@app.route("/poll")
def poll():
    result = []
    result.append("tilt " + str(req.direction))
    for id in busy:
      result.append("_busy " + id)      
    return "\n".join(result)

@app.errorhandler(Exception)
def all_exception_handler(error):
   logging.error(traceback.format_exc())
   return 'Error', 500

if __name__ == "__main__":
    app.run(port=17311, threaded=True)
