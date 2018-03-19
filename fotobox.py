import tweepy
from time import sleep
import RPi.GPIO as GPIO
import picamera
import configparser
import os
from datetime import datetime


# Setup Config
config = configparser.ConfigParser()
config.read('config.ini')
print('read the config')

pin_camera_btn = int(config['CONFIGURATION']['pin_camera_btn'])
pin_confirm_btn = int(config['CONFIGURATION']['pin_confirm_btn'])
pin_cancel_btn = int(config['CONFIGURATION']['pin_cancel_btn'])
prep_delay = int(config['CONFIGURATION']['prep_delay'])
photo_w = int(config['CONFIGURATION']['photo_w'])
photo_h = int(config['CONFIGURATION']['photo_h'])
screen_w = int(config['CONFIGURATION']['screen_w'])
screen_h = int(config['CONFIGURATION']['screen_h'])

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_camera_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_confirm_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_cancel_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

debounce = 0.05  # Min duration (seconds) button is required to be "pressed in" for.


# Setup Camera

camera = picamera.PiCamera()
#camera.rotation = 270
camera.resolution = (photo_h, photo_w)
#camera.hflip = True

def get_filename():
    filename = "/pictures/" + str(datetime.now()).split('.')[0]
    filename = filename.replace(' ', '_')
    filename = filename.replace(':', '-')
    filename += ".jpg"
    return filename



def take_picture():
    print("took a picture")
    filename = get_filename()
    camera.capture(filename)


def main():
    print("startup")
    print("press the button to take a photo")

    camera.start_preview(resolution=(screen_w,screen_h))
    sleep(10)
    while True:
        input_state = GPIO.input(pin_camera_btn)
        if input_state == False:
            sleep(debounce)
            if input_state == False:
                print("took a picture")
                take_picture()
                sleep(0.05)

try:
    main()
except KeyboardInterrupt:
    print("goodbye")

except Exception as exception:
    print("unexpected error: ", str(exception))

finally:
    camera.stop_preview()
    camera.close()
    GPIO.cleanup()