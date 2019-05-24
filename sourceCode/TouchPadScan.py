from machine import Pin, TouchPad
import time

keys = []
for pin in range(40):
	try:
		touchPad = TouchPad(Pin(pin))
	except ValueError:
		continue
	keys.append((pin, touchPad))
while True:
	for pin, touchPad in keys:
		print("[{}]: {}".format(pin, touchPad.read()), end=" ")
	print()
	time.sleep(0.5)


