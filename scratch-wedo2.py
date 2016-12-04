#!/usr/bin/env python

import sys
import random
import traceback
import logging

from gattlib import GATTRequester
from time import sleep
from struct import pack
from flask import Flask

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

ADDRESS = sys.argv[1]
HANDLE = 0x3d

motorPower = {}
busy = {}

req = GATTRequester(ADDRESS, False)

req.connect(True)

@app.route("/crossdomain.xml")
def crossdomain():
    return '''
        <cross-domain-policy>
          <allow-access-from domain="*" to-ports="<yourPort>"/>
        </cross-domain-policy>
    '''

@app.route("/reset_all")
def reset():
    req.write_by_handle(HANDLE, "\x06\x04\x01\x00")
    return ""

@app.route("/setLight/<color>")
def setLight(color):
    COLORS = ( "off", "pink", "purple", "blue", "sky blue", "teal", "green", "yellow", "orange", "red", "white")

    if color == "random":
      color = random.randint(1,10)
    else:
      color = COLORS.index(color)

    print("Set light color to " + str(color))
    
    req.write_by_handle(HANDLE, "\x06\x04\x01" + chr(color))
    return ""

#/motorOnFor/19/motor%20A/2
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
    req.write_by_handle(HANDLE, pack("<bbbb", 0x01, 0x01, 0x01, int(motorPower.get(motor, 50))))
    sleep(float(duration))
    del busy[id]
    print "Stop"
    
    req.write_by_handle(HANDLE, "\x01\x01\x01\x00")
    return ""

@app.route("/poll")
def poll():
    result = []
    for id in busy:
      result.append("_busy " + id)      
    return "\n".join(result)

@app.errorhandler(Exception)
def all_exception_handler(error):
   logging.error(traceback.format_exc())
   return 'Error', 500

if __name__ == "__main__":
    app.run(port=17311, threaded=True)
