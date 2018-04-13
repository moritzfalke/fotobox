
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
    camera.annotate_text = ""
    camera.capture(filename)
    print("took a picture")
    img = Image.open(filename)
    pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
    ))
    pad.paste(img, (0, 0))
    o = camera.add_overlay(pad.tobytes(), size=img.size)
    o.alpha = 255
    o.layer = 3
    if(twitter_enabled):
        camera.remove_overlay(o)
        ready_for_tweet(filename)
    else:
        sleep(5)
        camera.remove_overlay(o)
    sleep(1)

def tweet(filename):
    twitter.update_with_media(filename, 'test')

def ready_for_tweet(filename):

    img = Image.open(filename)
    pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
    ))
    pad.paste(img, (0, 0))
    o = camera.add_overlay(pad.tobytes(), size=img.size)
    o.alpha = 255
    o.layer = 3

    img = Image.open('tweet.jpg')
    padnew = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
    ))
    padnew.paste(img, (0, 0))
    onew = camera.add_overlay(pad.tostring(), size=img.size)
    onew.alpha = 128
    onew.layer = 4
    sleep(4)
    camera.remove_overlay(onew)
   # camera.annotate_text = "Do you want to tweet the picture? Press the green button for yes and the red Button to cancel"
    print("Do you want to tweet the picture?")
    while True:
        input_state_confirm = GPIO.input(pin_confirm_btn)
        input_state_cancel = GPIO.input(pin_cancel_btn)
        if input_state_confirm == False:
            sleep(debounce)
            if input_state_confirm == False:
                print("tweeting")
                tweet(filename)
                camera.annotate_text = "tweeted successfully!"
                sleep(1)
                camera.annotate_text = ""
                camera.remove_overlay(o)
                break
        elif input_state_cancel == False:
            sleep(debounce)
            if input_state_cancel == False:
                print("cancelled tweeting")
                camera.annotate_text = "Did not tweet"
                sleep(1)
                camera.annotate_text = ""
                camera.remove_overlay(o)
                break
        sleep(0.05)
    print("finished ready for tweet")

def main():
    print("startup")
    camera.start_preview(resolution=(screen_w,screen_h))
    camera.annotate_text = "Press the bottom red Button to take a picture!"
    print("press the button to take a photo")
    while True:
        input_state = GPIO.input(pin_camera_btn)
        if input_state == False:
            sleep(debounce)
            if input_state == False:
                camera.annotate_text = ""
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
