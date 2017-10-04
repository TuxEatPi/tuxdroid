import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# TODO dynamize it

GPIO.setup(16, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.output(16, GPIO.LOW)
GPIO.output(25, GPIO.LOW)
GPIO.output(19, GPIO.LOW)
GPIO.output(13, GPIO.LOW)

GPIO.cleanup()
