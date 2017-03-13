#!/usr/bin/env python

import time, serial, os, sys
from sys import stderr


class FakeSerial:

	# Base class for mock versions of serial.Serial
	# Does not inherit from serial.Serial, merely imitates it
	# This DOES NOT behave in a really similar way to reak hardware serial ports; it is built to
	# give you canned test data.
	# I never thought I'd miss Java interfaces

	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		self.timeout = timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.break_condition = False;
		self.cmdToFile = {}
		self.cmdToDataLength = {}
		# in a real implementation, there should be filehandles in there
		stderr.write("\tFake serial port initialized\n")

	def open(self):
		# if test file is not open, open it
		for fileHandle in self.cmdToFile.values():
			if fileHandle.closed:
				fileHandle = open(fileHandle.name)

	def close(self):
		for fileHandle in self.cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()

	def __del__(self):
		for fileHandle in self.cmdToFile.values():
			if not fileHandle.closed:
				fileHandle.close()

	def read(self, size=1):
		# read *size* bytes from the file
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

	# TODO: handle the rest of the methods, so we don't have any weird unexpected behavior here!


class MockPirani(FakeSerial):

	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		self.timeout = timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.name = "mockpirani"
		self.cmdToDataLength = {
			"@253U?;FF":14, # get units
			"@253PR1?;FF":17, # read pressure
		}
		unitFileName = os.path.dirname(os.path.realpath(__file__))+"/testPiraniUnits.dat"
		uf = open(unitFileName, 'r')
		pressureFileName = os.path.dirname(os.path.realpath(__file__))+"/testPiraniPressure.dat"
		pf = open(pressureFileName, 'r')
		self.cmdToFile = {
			"@253U?;FF":uf,
			"@253PR1?;FF":pf
		}
		sys.stderr.write("\tMock serial port to Pirani initialized\n")

class MockCapacitance(FakeSerial):
	def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
		self.timeout = timeout
		if self.timeout is None:
			self.timeout = 30 # sanity
		self.lastCmd = None
		self.name = "mockcapacitance"
		self.cmdToDataLength = {
			"u":4, # get units TODO GET CORRECT VALUES HERE!
			"p":13, # read pressure
			"f":13 # fullscale
		}
		unitFileName = os.path.dirname(os.path.realpath(__file__))+"/testCapUnits.dat"
		uf = open(unitFileName, 'r')
		pressureFileName = os.path.dirname(os.path.realpath(__file__))+"/testCapPressure.dat"
		pf = open(pressureFileName, 'r')
		fullscaleFileName = os.path.dirname(os.path.realpath(__file__))+"/testCapFullscale.dat"
		ff = open(fullscaleFileName, 'r')
		self.cmdToFile = {
			"u":uf,
			"p":pf,
			"f":ff,
		}
		sys.stderr.write("\tMock serial port to capacitance gauge initialized\n")
