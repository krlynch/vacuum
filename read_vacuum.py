#!/usr/bin/env python

import os, serial, sys, signal, select, time, datetime
from tests.fakeSerial import MockPirani, MockCapacitance
from pressure_gauges import Pirani, Capacitance
import matplotlib.pyplot as plt



class VacuumReader(object):
    """ Stores information about the connections to the pressure gauges and the file to write pressure data to.
    Utility methods for setting up connections, cleaning them up, keeping time, and writing to the data file. 
    To interact with the gauges themselves, use the variables 'pirani' and 'capacitance'"""

    pirani_port_templ = "/dev/ttyUSB%1d"
    capacitance_port_templ = "/dev/ttyUSB%1d"
    isoformat = "%Y-%m-%d-%H-%M-%S"

    def __init__(self, chamber, debug):
        """ Establishes if you are in test mode, and if you are debugging.
        arguments: 
        chamberNum -- 1, 2, or -1. -1 indicates test mode
        debug -- True to print debug statements, False othrwise """
        self.pirani = None
        self.capacitance = None
        self.outfile = None
        self.chamber = chamber
        self.testMode = (chamber == -1)
        self.debug = debug
        self.capacitance_fullscale = [1000.,1.]
        self.capacitance_minscale = [1e-1, 1.e-4]
        self.pirani_units = "torr"
        self.capacitance_units = "torr"
        self.starttime = None

    def setUpOutfile(self, filename):
        """ Opens the specified file; saves a filehandle in self.outfile """
        self.outfile = open(filename, 'w')

    def setUpPirani(self):  
        """ Creates a connection to the Pirani gauge via pySerial, unless in test mode.
        In test mode, creates a connection to a mockup pirani gauge using MockPirani.
        The Pirani instance can be accessed via self.pirani """
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
        """ Creates a connection to the capacitance gause via pySerial, unless in test mode.
        In test mode, creates a connection to a mockup capacitance gauge using MockCapacitance.
        The Capacitance instance can be accessed via self.capacitance """
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
        """ Write string ostr to both the output file and stdout """
        self.outfile.write(ostr)
        self.outfile.flush()
        sys.stdout.write(ostr)
        sys.stdout.flush()

    def closeAll(self):
        """ Closes output file, and connections to both gauges """
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
    """ All setup necessary to begin reading the pressure.

    arguments: 
    chamberNum -- (1, 2, or -1. -1 indicates test mode)

    Creates an instance of VacuumReader, establishes connections to pressure gauges (real or mock), creates an output file.
    Writes header data (column names, etc) for the output file, gets the units of measurement from the gauges, and sets the 
    measurement start time.
    RETURNS: the vacuumReader object """
    
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
    reader.pirani_units = pirani_units
    reader.capacitance_units = capacitance_units
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

    sys.stdout.write("VACUUM READER\n***********\nPressure data will be live-plotted. Please save the plot manually before exiting vacuum_reader\n**********\n")
    reader = setUp(int(sys.argv[1]))
    delaytime = 9.0 # inter-measurement delay time
    try:
        # start data collection
        timeAxis = []
        piraniVals = []
        capVals_1 = []
        capVals_2 = []
        figure = plt.figure(1)
        plt.ion()
        plt.show()

        while True:
            pirani_val = reader.pirani.getPressure()[0]
            capacitance_val = reader.capacitance.getPressure()
            timeT = reader.timeElapsed()
            ostr = "%s\t%d\t%.02e\t%.02e\t%.02e\n" % (reader.isonow(), timeT, pirani_val, capacitance_val[0], capacitance_val[1])
            reader.teeWrite(ostr)

            timeAxis.append(timeT)
            piraniVals.append(pirani_val)
            capVals_1.append(capacitance_val[0])
            capVals_2.append(capacitance_val[1])
            figure.clear()
            lines = plt.plot(timeAxis, piraniVals, timeAxis, capVals_1, timeAxis, capVals_2)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Pressure')
            plt.title('Pressure in chamber')
            plt.legend(lines, ('Pirani ({0})'.format(reader.pirani_units), 'capacitance 0 ({0})'.format(reader.capacitance_units), 'capacitance 1 ({0})'.format(reader.capacitance_units)))
            plt.draw()
            plt.pause(delaytime)

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
