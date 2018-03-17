import tweepy
from time import sleep
import RPi.GPIO as GPIO
import picamera
import configparser
import os

# Setup Config
config = configparser.ConfigParser()
config.read('config.ini')

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
camera.rotation = 270
camera.resolution = (photo_h, photo_w)
camera.hflip = True

# Path
REAL_PATH = os.path.dirname(os.path.realpath(__file__))


def main():
    print("startup")
    print("press the button to take a photo")

    camera.start_preview(resolution=(screen_w,screen_h))
    sleep(10)


if __name__ == "__main__":
    main()
