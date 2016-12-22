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
HANDLE_BATTERY_LEVEL = 0x48

HANDLE_CCC_BUTTON = 0x12
HANDLE_CCC_PORT = 0x16
HANDLE_CCC_SENSOR_VALUE = 0x33
HANDLE_CCC_BATTERY_LEVEL = 0x49

TYPE_MOTOR = 0x1
TYPE_VOLTAGE = 0x14
TYPE_CURRENT = 0x15
TYPE_PIEZO_TONE = 0x16
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
        self.piezoTone = 0
        self.sensor = [0] * 7
        self.button = 0
        self.direction = 0
        self.distance = 10
        self.voltage = 0
        self.current = 0
        self.battery_level = 100

    def on_notification(self, handle, data):

        data = data[3:]
        
        if handle == HANDLE_PORT:
            port, attach = unpack("<BB", data[0:2])            
            if attach: 
                print("Notification on handle: {} {} {}".format(hex(handle), len(data), binascii.hexlify(data)))

                hubIndex, type = unpack("<BB", data[2:4])
                self.sensor[port] = type

                if type == TYPE_TILT:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_TILT, TILT_SENSOR_MODE_TILT, 1, INPUT_FORMAT_UNIT_RAW, 1))
                elif type == TYPE_MOTION:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_MOTION, 0, 1, INPUT_FORMAT_UNIT_RAW, 1))
                elif type == TYPE_MOTOR:
                    self.motor = port
                elif type == TYPE_VOLTAGE:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_VOLTAGE, 0, 30, INPUT_FORMAT_UNIT_SI, 1))
                elif type == TYPE_CURRENT:
                    self.write_without_response_by_handle(HANDLE_INPUT_COMMAND, pack("<BBBBBIBB", COMMAND_ID_INPUT_FORMAT, COMMAND_TYPE_WRITE, port, TYPE_CURRENT, 0, 30, INPUT_FORMAT_UNIT_SI, 1))
                elif type == TYPE_PIEZO_TONE:
                    self.piezoTone = port

        elif handle == HANDLE_SENSOR_VALUE:
            revision = unpack("<B", data[0:1])
            data = data[1:]
            while data:
              port = unpack("<B", data[0:1])[0]
              if self.sensor[port] == TYPE_TILT:
                self.direction = unpack("<B", data[1:2])[0]
                data = data[2:]
              elif self.sensor[port] == TYPE_MOTION:
                print("Notification on handle: {} {} {}".format(hex(handle), len(data), binascii.hexlify(data)))
                self.distance = unpack("<B", data[1:2])[0]
                print "distance " + str(self.distance)
                data = data[2:]
              elif self.sensor[port] == TYPE_VOLTAGE:
                self.voltage = unpack("<f", data[1:5])[0]                
                data = data[5:]
              elif self.sensor[port] == TYPE_CURRENT:
                self.current = unpack("<f", data[1:5])[0]                
                data = data[5:]
              else:
                break
        elif handle == HANDLE_BUTTON:
            self.button = unpack("<B", data[0])[0]
        elif handle == HANDLE_BATTERY_LEVEL:
            self.battery_level = unpack("<B", data[0])[0]
        else:
            print("Notification on handle: {} {} {}".format(handle, len(data), binascii.hexlify(data)))

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

ADDRESS = sys.argv[1]

motorDirection = {}
motorPower = {}
busy = {}

req = Requester(ADDRESS, False)

req.connect(True)

req.write_without_response_by_handle(HANDLE_CCC_BUTTON, pack("<h", 0x0001))
req.write_without_response_by_handle(HANDLE_CCC_PORT, pack("<h", 0x0001))
req.write_without_response_by_handle(HANDLE_CCC_SENSOR_VALUE, pack("<h", 0x0001))
req.write_without_response_by_handle(HANDLE_CCC_BATTERY_LEVEL, pack("<h", 0x0001))

@app.route("/crossdomain.xml")
def crossdomain():
    return '''
        <cross-domain-policy>
          <allow-access-from domain="*" to-ports="<yourPort>"/>
        </cross-domain-policy>
    '''

@app.route("/reset_all")
def reset():
    req.write_without_response_by_handle(HANDLE_OUTPUT_COMMAND, "\x06\x04\x01\x00")
    return ""

@app.route("/setLight/<color>")
def setLight(color):
    COLORS = ( "off", "pink", "purple", "blue", "sky blue", "teal", "green", "yellow", "orange", "red", "white")

    if color == "random":
      color = random.randint(1,10)
    else:
      color = COLORS.index(color)

    print("Set light color to " + str(color))
    
    req.write_without_response_by_handle(HANDLE_OUTPUT_COMMAND, "\x06\x04\x01" + chr(color))
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
    print "motor on " + str(motorDirection.get(motor, 1) * motorPower.get(motor, 50))
    sleep(1.0/30.0)
    print "go"
    req.write_without_response_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbb", req.motor, 0x01, 0x01, motorDirection.get(motor, 1) * motorPower.get(motor, 50)))
    
    return ""

@app.route("/motorOff/<motor>")
def motorOff(motor):
    req.write_without_response_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbb", req.motor, 0x01, 0x01, 0))
    print
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

@app.route("/playSound/<id>/<note>/<octave>/<duration>")
def playSound(id, note, octave, duration):
    NOTES = [ "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" ]
    octave = float(octave)
    note = float(NOTES.index(note))
    # https://en.wikipedia.org/wiki/Equal_temperament
    frequency = round(440.0 * 2 ** (((octave - 4) * 12 + note - 9) / 12))
    duration = float(duration)
    print str(note) + " " + str(octave) + " " + str(frequency) + " " + str(duration)
    req.write_without_response_by_handle(HANDLE_OUTPUT_COMMAND, pack("<bbbhh", req.piezoTone, 0x02, 0x04, frequency, round(duration * 1000.0)))
    busy[id] = True
    sleep(duration - 1.0/30.0)
    del busy[id]

    return ""

@app.route("/poll")
def poll():
    BUTTON_STR = ('false', 'true')
    TILT_STR = ( "any", "any", "any", "up", "any", "right", "any", "left", "any", "down", "any" )

    result = []
    result.append("button1 " + BUTTON_STR[req.button])
    result.append("tilt " + TILT_STR[req.direction])
    result.append("distance " + str(req.distance))
    result.append("voltage1 " + str(int(req.voltage)))
    result.append("current1 " + str(int(req.current)))
    result.append("battery1 " + str(req.battery_level))
    for id in busy:
      result.append("_busy " + id)
    return "\n".join(result)

@app.errorhandler(Exception)
def all_exception_handler(error):
   logging.error(traceback.format_exc())
   return 'Error', 500

if __name__ == "__main__":
    app.run(port=17311, threaded=True)
