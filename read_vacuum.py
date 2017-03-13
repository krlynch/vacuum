#!/usr/bin/env python

import os, serial, sys, signal, select, time, datetime
from tests.fakeSerial import MockPirani, MockCapacitance
from pressure_gauges import Pirani, Capacitance



class VacuumReader(object):
    pirani_port_templ = "/dev/ttyUSB%1d"
    capacitance_port_templ = "/dev/ttyUSB%1d"
    isoformat = "%Y-%m-%d-%H-%M-%S"

    def __init__(self, chamber, debug):
        self.pirani = None
        self.capacitance = None
        self.outfile = None
        self.chamber = chamber
        self.testMode = (chamber == -1)
        self.debug = debug
        self.capacitance_fullscale = [1000.,1.]
        self.capacitance_minscale = [1e-1, 1.e-4]
        self.starttime = None

    def setUpOutfile(self, filename):
        self.outfile = open(filename, 'w')

    def setUpPirani(self):  
        pirani_serial = None 
        if self.testMode:
            pirani_serial = MockPirani("TEST_PIRANI", 9600, 8, 'N', 1)
        elif self.chamber == 1:
            pirani_port = self.pirani_port_templ % (0)
            pirani_serial = serial.Serial(pirani_port, 9600, 8, 'N', 1)
        elif self.chamber == 2:
            pirani_port = self.pirani_port_templ % (2)
            pirani_serial = serial.Serial(pirani_port, 9600, 8, 'N', 1)
        else: 
            raise no_system(self.chamber)
        self.pirani = Pirani(pirani_serial, self.debug)
        self.pirani.flush()

    def setUpCapacitance(self):
        cap_serial = None 
        if self.testMode:
            cap_serial = MockCapacitance("TEST_CAP", 9600, 8, 'N', 1)
        elif self.chamber == 1:
            cap_port = self.capacitance_port_templ % (0)
            cap_serial = serial.Serial(cap_port, 9600, 8, 'N', 1)
        elif self.chamber == 2:
            cap_port = self.capacitance_port_templ % (2)
            cap_serial = serial.Serial(cap_port, 9600, 8, 'N', 1)
        else: 
            raise no_system(self.chamber)
        self.capacitance = Capacitance(cap_serial, self.debug)
        self.capacitance.setFullscaleManual(self.capacitance_fullscale)
        self.capacitance.setMinscaleManual(self.capacitance_minscale)
        self.capacitance.flush()

    def isonow(self):
        n = datetime.datetime.now()
        return n.strftime(self.isoformat)

    def timeElapsed(self):
        later = self.isonow()
        earlier = self.starttime
        if self.debug:
            sys.stderr.write("elapsed\n")
            sys.stderr.flush()
        l = datetime.datetime.now()
        l = l.strptime(later, self.isoformat)
        e = l.strptime(earlier, self.isoformat)
        diff = (l-e).total_seconds()
        if self.debug:
            sys.stderr.write("\tlater: %s\n" % l)
            sys.stderr.write("\tearlier: %s\n" % e)
            sys.stderr.write("\tdiff: %d\n" % diff)
            sys.stderr.flush()
        return diff

    
    def teeWrite(self, ostr):
        self.outfile.write(ostr)
        self.outfile.flush()
        sys.stdout.write(ostr)
        sys.stdout.flush()

    def closeAll(self):
        if self.outfile != None:
            sys.stderr.write("\tClosing output file ....\n")
            sys.stderr.flush()
            self.outfile.close()
        # code duplication ... ick
        if self.pirani != None:
            sys.stderr.write("\tClosing Pirani serial port ....\n")
            sys.stderr.flush()
            self.pirani.close()
        if self.capacitance != None:
            sys.stderr.write("\tClosing Capacitance Manometer serial port ....\n")
            sys.stderr.flush()
            self.capacitance.close()







def setUp(chamberNum):
    
    reader = VacuumReader(chamberNum, False)
    reader.setUpPirani()
    reader.setUpCapacitance()

    oname = "vacuum-%s.csv" % reader.isonow()
    reader.setUpOutfile(oname)

    if reader.testMode:
        ostr = "RUNNING IN TEST MODE -- NO REAL DATA FOLLOWS\n"
        reader.teeWrite(ostr)

    ostr = "# Opened %s for output\n" % oname
    reader.teeWrite(ostr)

    ostr = "# Format Version: 3.0\n"
    reader.teeWrite(ostr)

    ostr = "# Columns: DateTime [localtime];Elapsed [s];Pirani; High Range Capacitance Manometer; Low Range Capacitance Manometer\n"
    reader.teeWrite(ostr)

    pirani_units = reader.pirani.getUnits()
    capacitance_units = reader.capacitance.getUnits()
    #capacitance_fullscale = read_capacitance_fullscale()
    print(reader.capacitance.getFullscale())
    ostr = "# Gauge Units: %s %s\n" % (pirani_units,capacitance_units)
    reader.teeWrite(ostr)

    reader.starttime = reader.isonow()
    return reader


def handleExit(signal, frame):
    raise SystemExit


class no_serial(Exception):
    def __init__(self, port):
        self.port = port
    def __str__(self):
        return repr("No Serial Port: %s" % self.port)

class no_system(Exception):
    def __init__(self, sys_num):
        self.sys_num = sys_num
    def __str__(self):
        return repr("No Vacuum System: %s" % self.sys_num)


if __name__ == '__main__':
    signal.signal(signal.SIGHUP, handleExit)
    signal.signal(signal.SIGINT, handleExit)
    signal.signal(signal.SIGQUIT, handleExit)
    signal.signal(signal.SIGTERM, handleExit)
    
    reader = setUp(int(sys.argv[1]))
    delaytime = 10.0 # inter-measurement delay time
    try:
        # start data collection
        while True:
            pirani_val = reader.pirani.getPressure()[0]
            capacitance_val = reader.capacitance.getPressure()
            ostr = "%s\t%d\t%.02e\t%.02e\t%.02e\n" % (reader.isonow(), reader.timeElapsed(), pirani_val, capacitance_val[0], capacitance_val[1])
            reader.teeWrite(ostr)
            if select.select([sys.stdin],[],[],delaytime)[0]:
                readlines(sys.stdin)
            else:
                continue
    except NameError:
        None
    except SystemExit:
        None
    except no_system as ns:
        sys.stderr.write('No vacuum system numbered %d\n' % ns.sys_num)
        sys.stderr.flush()
    except:
        sys.stderr.write("Caught Unexpected Exception: %s\n" % sys.exc_info()[0])
        sys.stderr.write("%s\n" % sys.exc_info()[1])
        sys.stderr.flush()

    reader.closeAll()
