#!/usr/bin/env python

import time, serial
from sys import stderr


class FakeSerial:

	# Base class for mock versions of serial.Serial
	# Does not inherit from serial.Serial, merely imitates it
	# This DOES NOT behave in a really similar way to reak hardware serial ports; it is built to
	# give you canned test data.
	# I never thought I'd miss Java interfaces

	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		# if port is given, open input file, save input file handle
		self.timeout = timeout
		self.port = port
		self.baudrate = baudrate
		self.bytesize = bytesize
		self.parity = parity
		self.stopbits = stopbits
		self.xonxoff = xonxoff
		self.rtscts = rtscts
		self.write_timeout = write_timeout
		self.dsrdtr = dsrdtr
		self.inter_byte_timeout = inter_byte_timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.break_condition = False;
		self.cmdToFile = {}
		self.cmdToDataLength = {}
		self._isOpen = False;
		# in a real implementation, there should be filehandles in there
		stderr.write("\tFake serial port initialized\n")

	def open(self):
		# if test file is not open, open it
		for fileHandle in self.cmdToFile.values():
			if fileHandle.closed:
				fileHandle = open(fileHandle.name)
		self._isOpen = True;
		self._isOpen = True

	def close(self):
		for fileHandle in self.cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()
		self._isOpen = False;

	def __del__(self):
		for fileHandle in self.cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()
		self._isOpen = False;

	def read(self, size=1):
		# read *size* bytes from the file
		# if not enough bytes, block until either timeout is reached or more bytes appear
		# clear last command when done
		out = ""
		if self.lastCmd is None or self.lastCmd not in self.cmdToFile:
			time.sleep(self.timeout)
		else:
			f = self.cmdToFile[self.lastCmd]
			out = f.read(size)
		self.lastCmd = None
		return out

	def write(self, data):
		self.lastCmd = data;
		return len(data)

	def flush(self):
		# leave this, we prob don't need it for our purposes
		pass

	def inWaiting(self):
		# reads how many bytes are waiting in the input buffer -- depends on current command sent
		if self.lastCmd is None or self.lastCmd not in self.cmdToDataLength:
			return 0
		else:
			return self.cmdToDataLength[self.lastCmd]


	def outWaiting(self):
		return 0

	def flushInput(self):
		# do nothing
		pass

	def flushOutput(self):
		# do nothing
		pass

	def reset_input_buffer(self):
		pass

	def reset_output_buffer(self):
		pass

	def send_break(self):
		pass

	# TODO: handle the rest of the methods, so we don;t have any weird unexpected behavior here!


class MockPirani(FakeSerial):

	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		# if port is given, open input file, save input file handle
		self.timeout = timeout
		self.port = port
		self.baudrate = baudrate
		self.bytesize = bytesize
		self.parity = parity
		self.stopbits = stopbits
		self.xonxoff = xonxoff
		self.rtscts = rtscts
		self.write_timeout = write_timeout
		self.dsrdtr = dsrdtr
		self.inter_byte_timeout = inter_byte_timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.break_condition = False
		self.name = "mockpirani"
		self.cmdToDataLength = {
			"@253U?;FF":14, # get units
			"@253PR1?;FF":17, # read pressure
		}
		unitFileName = "testPiraniUnits.dat"
		uf = open(unitFileName, 'r')
		pressureFileName = "testPiraniPressure.dat"
		pf = open(pressureFileName, 'r')
		self.cmdToFile = {
			"@253U?;FF":uf,
			"@253PR1?;FF":pf
		}
		self._isOpen = True
		stderr.write("\tMock serial port to Pirani initialized\n")

class MockCapacitance(FakeSerial):
	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		# if port is given, open input file, save input file handle
		self.timeout = timeout
		self.port = port
		self.baudrate = baudrate
		self.bytesize = bytesize
		self.parity = parity
		self.stopbits = stopbits
		self.xonxoff = xonxoff
		self.rtscts = rtscts
		self.write_timeout = write_timeout
		self.dsrdtr = dsrdtr
		self.inter_byte_timeout = inter_byte_timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.break_condition = False
		self.name = "mockpirani"
		self.cmdToDataLength = {
			"u":4, # get units TODO GET CORRECT VALUES HERE!
			"p":13, # read pressure
			"f":25 # fullscale
		}
		unitFileName = "testCapUnits.dat"
		uf = open(unitFileName, 'r')
		pressureFileName = "testCapPressure.dat"
		pf = open(pressureFileName, 'r')
		fullscaleFileName = "testCapFullscale.dat"
		ff = open(fullscaleFileName, 'r')
		self.cmdToFile = {
			"u":uf,
			"p":pf,
			"f":ff,
		}
		self._isOpen = True
		stderr.write("\tMock serial port to capacitance gauge initialized\n")
