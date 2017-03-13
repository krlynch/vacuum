#!/usr/bin/env python

from sys import stderr
from serial import Serial
import time

class ack_error(Exception):
    def __init__(self, ack):
        self.ack = ack

    def __str__(self):
        return repr("Bad ack: %s" % self.ack)

class PressureGauge(object):

    unitsCommand = "none"
    pressureCommand = "none"
    waittime = 0.05

    def __init__(self, serialInstance, debug):
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