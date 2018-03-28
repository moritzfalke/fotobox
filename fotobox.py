
import tweepy
from time import sleep
import RPi.GPIO as GPIO
import picamera
import configparser
import os
from datetime import datetime
from PIL import Image

REAL_PATH = os.path.dirname(os.path.realpath(__file__))

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

# Setup Twitter
twitter_enabled = (config['TWITTER']['enable'] == 'X')
always_hastags = config['TWITTER']['always_hashtags']
hashtags_amount = config['TWITTER']['hashtags_amount']
consumer_key = config['TWITTER']['consumer_key']
consumer_secret = config['TWITTER']['consumer_secret']
access_token = config['TWITTER']['access_token']
access_token_secret = config['TWITTER']['access_token_secret']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
twitter = tweepy.API(auth)


# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_camera_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_confirm_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_cancel_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

debounce = 0.02  # Min duration (seconds) button is required to be "pressed in" for.


# Setup Camera

camera = picamera.PiCamera()
#camera.rotation = 270
camera.resolution = (photo_h, photo_w)
#camera.hflip = True

def get_filename():
    filename = REAL_PATH + "/pictures/" + str(datetime.now()).split('.')[0]
#    filename = "/pictures/" + str(datetime.now()).split('.')[0]
    filename = filename.replace(' ', '_')
    filename = filename.replace(':', '-')
    filename += ".jpg"
    return filename



def take_picture():
    for x in range(prep_delay, 0 , -1):
        camera.annotate_text = ("      " + str(x) )
        print("picture in" + str( x))
        sleep(1)
    filename = get_filename()
    camera.capture(filename)
    print("took a picture")
    ready_for_tweet(filename)
#    if twitter_enabled:
#        tweet(filename)
    sleep(1)

def tweet(filename):
    twitter.update_with_media(filename, 'test')

def ready_for_tweet(filename):
    img = Image.open(filename)
    pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
        ))
#    pad = Image.new('RGB', (
#        ((img.size[0] +31) // 32) * 32,
#        ((img.size[1] + 15 // 16) *16,
#        ))
    pad.paste(img, (0,0))
    o = camera.add_overlay(pad.tobytes(), size = img.size)
    o.alpha = 128
    o.layer = 3
    while True:
        input_state_confirm = GPIO.input(pin_confirm_btn)
        input_state_cancel = GPIO.input(pin_cancel_btn)
        if input_state_confirm == False:
            sleep(debounce)
            if input_state_confirm == False:
                tweet(filename)
        elif input_state_cancel == False:
            sleep(debounce)
            if input_state_cancel == False:
                break
    sleep(0.05)

def main():
    print("startup")
    print("press the button to take a photo")

    camera.start_preview(resolution=(screen_w,screen_h))
    while True:
        input_state = GPIO.input(pin_camera_btn)
        if input_state == False:
            sleep(debounce)
            if input_state == False:
                take_picture()
        sleep(0.05)

try:
    main()
except KeyboardInterrupt:
    print("goodbye")

#except Exception as exception:
#    print("unexpected error: ", str(exception))

finally:
    camera.stop_preview()
    camera.close()
    GPIO.cleanup()
