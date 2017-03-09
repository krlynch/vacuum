#!/usr/bin/env python

import os, serial, sys, signal, select, time, datetime

pirani_port_templ = "/dev/ttyUSB%1d"
capacitance_port_templ = "/dev/ttyUSB%1d"

pirani = None
capacitance = None
outfile = None

waittime = 0.05 # wait between write/read for pirani
delaytime = 10.0 # inter-measurement delay time

capacitance_fullscale = [1000.,1.]
capacitance_minscale = [1e-1, 1.e-4]

debug=False

def cleanup(signal, frame):
    sys.stderr.write("Cleaning up ....\n")
    sys.stderr.flush()
    if outfile != None:
        sys.stderr.write("\tClosing output file ....\n")
        sys.stderr.flush()
        outfile.close()
    # code duplication ... ick
    if pirani != None:
        sys.stderr.write("\tClosing Pirani serial port ....\n")
        sys.stderr.flush()
        pirani.close()
    if capacitance != None:
        sys.stderr.write("\tClosing Capacitance Manometer serial port ....\n")
        sys.stderr.flush()
        capacitance.close()
    sys.exit(0)

signal.signal(signal.SIGHUP, cleanup)
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGQUIT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

isoformat = "%Y-%m-%d-%H-%M-%S"

def isonow():
    n = datetime.datetime.now()
    return n.strftime(isoformat)

def elapsed(later, earlier):
    if debug:
        sys.stderr.write("elapsed\n")
        sys.stderr.flush()
    l = datetime.datetime.now()
    l = l.strptime(later, isoformat)
    e = l.strptime(earlier, isoformat)
    diff = (l-e).total_seconds()
    if debug:
        sys.stderr.write("\tlater: %s\n" % l)
        sys.stderr.write("\tearlier: %s\n" % e)
        sys.stderr.write("\tdiff: %d\n" % diff)
        sys.stderr.flush()
    return diff

class ack_error(Exception):
    def __init__(self, ack):
        self.ack = ack

    def __str__(self):
        return repr("Bad ack: %s" % self.ack)

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

def flush_serial(port):
    if debug:
        sys.stderr.write("flush_serial\n")
        sys.stderr.flush()
    cnt = port.inWaiting()
    if cnt>0:
        port.read(cnt)

def read_pirani_resp(req, expected):
    if debug:
        sys.stderr.write("read_pirani_resp\n")
        sys.stderr.flush()
    pirani.write(req.encode())
    while True:
        time.sleep(waittime)
        cnt = pirani.inWaiting()
        if debug:
            sys.stderr.write("%d\n" % cnt)
            sys.stderr.flush()
        if cnt==0:
            continue
        if cnt>0 and cnt%expected != 0:
            continue
        response = pirani.read(cnt).decode('utf8')
        break
    addr = response[1:4]
    ack = response[4:7]
    val = response[7:expected-3]
    if debug:
        sys.stderr.write("%d %d %s %s %s %s\n" %(cnt, expected, response, addr, ack, val))
        sys.stderr.flush()
    if ack != 'ACK':
        raise ack_error(ack)
    return addr, ack, val.lstrip().rstrip()    

def read_pirani_units():
    if debug:
        sys.stderr.write("read_pirani_units\n")
        sys.stderr.flush()
    w = '@253U?;FF' # get units
    expected = 14
    addr, ack, val = read_pirani_resp(w, expected)
    return val

def read_pirani_pressure():
    if debug:
        sys.stderr.write("read_pirani_pressure\n")
        sys.stderr.flush()
    w = '@253PR1?;FF' # read pressure
    expected = 17
    addr, ack, val = read_pirani_resp(w, expected)
    return float(val)

def read_capacitance_resp(req):
    if debug:
        sys.stderr.write("read_capacitance_resp\n")
        sys.stderr.flush()
    capacitance.write(req.encode())
    while True:
        time.sleep(waittime)
        cnt = capacitance.inWaiting()
        if debug:
            sys.stderr.write("%d\n" % cnt)
            sys.stderr.flush()
        if cnt==0:
            continue
        response = capacitance.read(cnt).decode('utf8')
        break
    if debug:
        sys.stderr.write("%d %s\n" % (cnt, response))
        sys.stderr.flush()
    return response.lstrip().rstrip()

def read_capacitance_units():
    if debug:
        sys.stderr.write("read_capacitance_units\n")
        sys.stderr.flush()
    w = 'u'
    response = read_capacitance_resp(w)
    return response

def read_capacitance_fullscale():
    if debug:
        sys.stderr.write("read_capacitance_fullscale\n")
        sys.stderr.flush()
    w = 'f'
    response = read_capacitance_resp(w)
    ch1,ch2 = response.split()
    return float(ch1),float(ch2)

def glue_minus(response):
    if debug:
        sys.stderr.write("glue_minus\n")
        sys.stderr.flush()
    resp = response.split()
    out = ''
    for r in resp:
        out += r 
        if r=='-':
            continue
        else:
            out += ' '
    if debug:
        sys.stderr.write("out = %s\n" % out)
        sys.stderr.flush()
    return out

def read_capacitance_pressure():
    if debug:
        sys.stderr.write("read_capacitance_pressure\n")
        sys.stderr.flush()
    w = 'p'
    response = read_capacitance_resp(w)
    # fart ... if the values are all _positive_, the list has length
    # 2, as expected.  A _negative_ value, however, is set off with a
    # _space_, believe it or not.  Need to deal with that ... fart
    response = glue_minus(response)
    ch1,ch2 = response.split()
    if ch1=='Off':
        ch1 = capacitance_fullscale[0]
    if float(ch1)<capacitance_minscale[0]:
        ch1 = capacitance_minscale[0]
    if ch2=='Off':
        ch2 = capacitance_fullscale[1]
    if float(ch2)<capacitance_minscale[1]:
        ch2 = capacitance_minscale[1]
    return float(ch1),float(ch2)

try:
    sys.stderr.write("Starting up ....\n")
    sys.stderr.flush()
    # gross, icky hack!
    which_chamber = int(sys.argv[1])
    if which_chamber==1:
        pirani_port = pirani_port_templ % (0)
        capacitance_port = capacitance_port_templ % (1)
    elif which_chamber==2:
        pirani_port = pirani_port_templ % (2)
        capacitance_port = capacitance_port_templ % (3)
        capacitance_fullscale = [1000.,0.02]
        capacitance_minscale = [1e-1, 4.e-7]
    else:
        raise no_system(which_chamber)
    pirani = serial.Serial(pirani_port, 9600, 8, 'N', 1)
    if pirani == None:
        raise no_serial(pirani_port)
    capacitance = serial.Serial(capacitance_port, 9600, 8, 'N', 1)
    if capacitance == None:
        raise no_serial(capacitance_port)
    flush_serial(pirani)
    flush_serial(capacitance)
    
    sys.stderr.write("\tOpened %s for Pirani Gauge\n" % pirani_port)
    sys.stderr.flush()
    sys.stderr.write("\tOpened %s for Capacitance Manometers\n" % capacitance_port)
    sys.stderr.flush()

    oname = "vacuum-%s.csv" % isonow()
    outfile = open(oname, 'w')
    ostr = "# Opened %s for output\n" % oname
    outfile.write(ostr)
    outfile.flush()
    sys.stdout.write(ostr)
    sys.stdout.flush()

    ostr = "# Format Version: 3.0\n"
    outfile.write(ostr)
    outfile.flush()
    sys.stdout.write(ostr)
    sys.stdout.flush()

    ostr = "# Columns: DateTime [localtime];Elapsed [s];Pirani; High Range Capacitance Manometer; Low Range Capacitance Manometer\n"
    outfile.write(ostr)
    outfile.flush()
    sys.stdout.write(ostr)
    sys.stdout.flush()

    pirani_units = read_pirani_units()
    capacitance_units = read_capacitance_units()
    #capacitance_fullscale = read_capacitance_fullscale()
    print(read_capacitance_fullscale())
    ostr = "# Gauge Units: %s %s\n" % (pirani_units,capacitance_units)
    outfile.write(ostr)
    outfile.flush()
    sys.stdout.write(ostr)
    sys.stdout.flush()

    starttime = isonow()

    # start data collection
    while True:
        timenow = isonow()
        pirani_val = read_pirani_pressure()
        capacitance_val = read_capacitance_pressure()
        ostr = "%s\t%d\t%.02e\t%.02e\t%.02e\n" % (isonow(), elapsed(timenow, starttime), pirani_val, capacitance_val[0], capacitance_val[1])
        outfile.write(ostr)
        outfile.flush()
        sys.stdout.write(ostr)
        sys.stdout.flush()
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

cleanup(None, None)
