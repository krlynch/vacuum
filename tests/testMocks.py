#!/usr/bin/env/python

import sys
from fakeSerial import FakeSerial, MockPirani, MockCapacitance

# test for your tests
# this checks to see if the mock-Serial classes are working correctly

fails = []

# startup should happen with no errors
mockPirani = None
try:
	mockPirani = MockPirani("any_pirani_port", 9600, 8, 'N', 1)
except BaseException as err:
	print "FAILURE! Could not open MockPirani instance!"
	print "Error: {0}".format(err)
	sys.exit()

mockCap = None
try:
	mockCap = MockCapacitance("any_cap_port", 9600, 8, 'N', 1)
except BaseException as err:
	print "FAILURE! Could not open MockCapacitance instance!"
	print "Error: {0}".format(err)
	mockPirani.close()
	sys.exit()


# send a valid command, get a valid response: units
print "Test: write commands and read from Pirani"
print "\t... units"
mockPirani.write("@253U?;FF")
numWaiting = mockPirani.inWaiting()
if (numWaiting != 14):
	print "FAILURE! Requesting units, followes by calling inWaiting, should result in 14. Instead, got ", numWaiting
	fails.append("identify cmd-to-data-length, did not try reading correct data file (pirani, units)")
else:
	print "PASS: pirani units command-to-data-length"
	res = mockPirani.read(14)
	if (res != "MOCKACKTORRDUN"):
		print "FAILURE! Trying to read units. Should have gotten MOCKACKTORRDUN, instead got ", res
		fails.append("read correct data from file based on command (pirani, units)")
	else:
		print "PASS: pirani units reading correct data"


print "\t... pressure"
mockPirani.write("@253PR1?;FF")
numWaiting = mockPirani.inWaiting()
if (numWaiting != 17):
	print "FAILURE! Requesting units, followes by calling inWaiting, should result in 17. Instead, got ", numWaiting
	fails.append("identify cmd-to-data-length, did not try reading correct data file (pirani, pressure)")
else:
	print "PASS: pirani pressure command-to-data-length"
	res = mockPirani.read(17)
	if (res != "MOCKACK0.00001DUN"):
		print "FAILURE! Trying to read units. Should have gotten MOCKACK0.00001DUN, instead got ", res
		fails.append("read correct data from file based on command (pirani, pressure)")
	else:
		print "PASS: pirani pressure reading correct data"

mockPirani.close()


print "\nTest: write commands and read from capacitance gauges"
print "\t... units"
mockCap.write("u")
numWaiting = mockCap.inWaiting()
if (numWaiting != 4):
	print "FAILURE! Requesting capacitance units, followes by calling inWaiting, should result in 4. Instead, got ", numWaiting
	fails.append("identify cmd-to-data-length, did not try reading correct data file (capacitance, units)")
else:
	print "PASS: capacitance units command-to-data-length"
	res = mockCap.read(4)
	if (res != "Torr"):
		print "FAILURE! Trying to read capacitance units. Should have gotten Torr, instead got ", res
		fails.append("read correct data from file based on command (capacitance, units)")
	else:
		print "PASS: capacitance units reading correct data"

print "\t... pressure"
mockCap.write("p")
numWaiting = mockCap.inWaiting()
if (numWaiting != 13):
	print "FAILURE! Requesting units, followes by calling inWaiting, should result in 13. Instead, got ", numWaiting
	fails.append("identify cmd-to-data-length, did not try reading correct data file (capacitance, pressure)")
else:
	print "PASS: capacitance pressure command-to-data-length"
	res = mockCap.read(13)
	if (res != "000.01 0.0100"):
		print "FAILURE! Trying to read units. Should have gotten 000.01 0.0100, instead got ", res
		fails.append("read correct data from file based on command (capacitance, pressure)")
	else:
		print "PASS: capacitance pressure reading correct data"


mockCap.close()

print "TEST RESULTS"
print "Failures: ", len(fails)
for fail in fails:
	print fail
