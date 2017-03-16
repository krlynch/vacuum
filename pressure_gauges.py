#!/usr/bin/env python
""" 
Code for interacting with pressure gauges. Requires the computer to communicate with the gauge via a serial port.

Initialize the subclasses of PressureGauge with an instance of serial.Serial, connected to the gauge itself.
For testing purposes, initialize with an instance of MockPirani, MockCapacitance, or other subclass of MockSerial.

To extend to more gauges:
* Create a new subclass of PressureGauge
* In your subclass, override the class vaiables `unitsCommand` and `pressureCommand` with the commands appropriate for that gauge
* In the subclass, override _sendCmdGetResp(self, cmd) with the correct functionality to request and receive data from the gauge
* If your gauge can tell you more than just units and pressure, create new methods in your subclass that use _sendCmdGetResp(self, cmd) to get that information
 """

from sys import stderr
from serial import Serial
import time

class ack_error(Exception):
    def __init__(self, ack):
        self.ack = ack

    def __str__(self):
        return repr("Bad ack: %s" % self.ack)

class PressureGauge(object):
    """ 
    Base class for interacting with the pressure gauges via serial ports.
    Not intended to be used on its own. Use its subclasses Pirani or Capacitance instead 
    """

    unitsCommand = "none"
    pressureCommand = "none"
    waittime = 0.05

    def __init__(self, serialInstance, debug):
        """ 
        Constructor
        arguments:
        serialInstance -- either an instance of pySerial's serial.serial, or a subclass of FakeSerial (MockPirani or MockCapacitance) 
        debug -- true to print debugging statements, false otherwise"""
        self.debug = debug
        self.innerSerial = serialInstance

    def _sendCmdGetResp(self, cmd):
        stderr.WARN("WARN: _sendCMdGetResp is not implemented in base class PressureGauge\n")
        return "" # implement in subclasses

    def _cleanPressureFormat(self, rawData):
        stderr.WARN("WARN: _cleanPressureFormat is not implemented in base class PressureGauge\n")
        return "" # implement in subclasses

    def getUnits(self):
        return self._sendCmdGetResp(self.unitsCommand)

    def getPressure(self):
        """ 
        Requests the current pressure measurement from the gauge(s).

        Returns -- a LIST of floats

        If this object only communicates with one physical gauge, the list will have one element.
        Otherwise, there will be one element per gauge.
        """
        raw = self._sendCmdGetResp(self.pressureCommand)
        return self._cleanPressureFormat(raw)

    def flush(self):
        if self.debug:
            stderr.write("flush_serial\n")
            stderr.flush()
        cnt = self.innerSerial.inWaiting()
        if cnt>0:
            self.innerSerial.read(cnt)

    def close(self):
        self.innerSerial.close()


class Pirani(PressureGauge):
    """
    Class for interacting with a Pirani gauge. Initialize either with serial.Serial or MockPirani.
    Expects to be connected to a single gauge.
    """

    pressureCommand = '@253PR1?;FF'
    unitsCommand = '@253U?;FF'
    expectedLengths = {
            unitsCommand:14,
            pressureCommand:17
        }

    def _sendCmdGetResp(self, cmd):
        expected = self.expectedLengths[cmd]
        self.innerSerial.write(cmd.encode())
        while True:
            time.sleep(self.waittime)
            cnt = self.innerSerial.inWaiting()
            if self.debug:
                stderr.write("%d\n" % cnt)
                stderr.flush()
            if cnt==0:
                continue
            if cnt>0 and cnt%expected != 0:
                continue
            response = self.innerSerial.read(cnt).decode('utf8')
            break
        addr = response[1:4]
        ack = response[4:7]
        val = response[7:expected-3]
        if self.debug:
            sys.stderr.write("%d %d %s %s %s %s\n" %(cnt, expected, response, addr, ack, val))
            sys.stderr.flush()
        if ack != 'ACK':
            raise ack_error(ack)
        return val.lstrip().rstrip()

    def _cleanPressureFormat(self, rawData):
        return [float(rawData)]


class Capacitance(PressureGauge):
    """
    Class for interacting with a capacitance gauge. Initialize either with serial.Serial or MockCapacitance.
    Expects to be connected to a pair of gauges.
    """

    pressureCommand = 'p'
    unitsCommand = 'u'
    fullscaleCommand = 'f'

    def __init__(self, serialInstance, debug):
    	super(Capacitance, self).__init__(serialInstance, debug)
        # default values
        self.fullscale = [1000.,1.]
        self.minscale = [1e-1, 1.e-4]

    def _sendCmdGetResp(self, cmd):
        self.innerSerial.write(cmd.encode())
        while True:
            time.sleep(self.waittime)
            cnt = self.innerSerial.inWaiting()
            if self.debug:
                stderr.write("%d\n" % cnt)
                stderr.flush()
            if cnt==0:
                continue
            response = self.innerSerial.read(cnt).decode('utf8')
            break
        if self.debug:
            stderr.write("%d %s\n" % (cnt, response))
            stderr.flush()
        return response.lstrip().rstrip()

    def _glue_minus(self, response):
        if self.debug:
            stderr.write("glue_minus\n")
            stderr.flush()
        resp = response.split()
        out = ''
        for r in resp:
            out += r 
            if r=='-':
                continue
            else:
                out += ' '
        if self.debug:
            stderr.write("out = %s\n" % out)
            stderr.flush()
        return out

    def _cleanPressureFormat(self, rawData):
        # fart ... if the values are all _positive_, the list has length
        # 2, as expected.  A _negative_ value, however, is set off with a
        # _space_, believe it or not.  Need to deal with that ... fart
        response = self._glue_minus(rawData)
        ch1,ch2 = response.split()
        if ch1=='Off':
            ch1 = self.fullscale[0]
        if float(ch1)<self.minscale[0]:
            ch1 = self.minscale[0]
        if ch2=='Off':
            ch2 = self.fullscale[1]
        if float(ch2)<self.minscale[1]:
            ch2 = self.minscale[1]
        return [float(ch1),float(ch2)]


    def getFullscale(self):
        return self._sendCmdGetResp(self.fullscaleCommand)

    def setFullscaleManual(self, fullscale):
        # no input validation... don't put anything weird here!
        self.fullscale = fullscale

    def setMinscaleManual(self, minscale):
        # no input validation... don't put anything weird here!
        self.minscale = minscale