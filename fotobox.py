
import tweepy
from time import sleep
import RPi.GPIO as GPIO
import picamera
import configparser
import os
from datetime import datetime
from sys import exit as sys_exit
from PIL import Image

REAL_PATH = os.path.dirname(os.path.realpath(__file__))

# Setup Config
config = configparser.ConfigParser()
config.read('config.ini')
print('read the config')
try:
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
    if(twitter_enabled):
        always_hastags = config['TWITTER']['always_hashtags']
        hashtags_amount = config['TWITTER']['hashtags_amount']
        consumer_key = config['TWITTER']['consumer_key']
        consumer_secret = config['TWITTER']['consumer_secret']
        access_token = config['TWITTER']['access_token']
        access_token_secret = config['TWITTER']['access_token_secret']
except KeyError as exc:
    print('')
    print('ERROR:')
    print(' - Problems exist within configuration file.')
    print(' - The expected configuration item ' + str(exc) + ' was not found.')
#    print(' - Please refer to the example file [' + PATH_TO_CONFIG_EXAMPLE + '], for reference.')
    print('')
    sys_exit()



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

def remove_overlay(overlay_id):
    """
    If there is an overlay, remove it
    """
    if overlay_id != -1:
        camera.remove_overlay(overlay_id)


def overlay_image(image_path, duration=0, layer=3):
    """
    Add an overlay (and sleep for an optional duration).
    If sleep duration is not supplied, then overlay will need to be removed later.
    This function returns an overlay id, which can be used to remove_overlay(id).
    """

    # "The camera`s block size is 32x16 so any image data
    #  provided to a renderer must have a width which is a
    #  multiple of 32, and a height which is a multiple of
    #  16."
    #  Refer: http://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview

    # Load the arbitrarily sized image
    img = Image.open(image_path)

    # Create an image padded to the required size with mode 'RGB'
    pad = Image.new('RGBA', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
    ))

    # Paste the original image into the padded one
    pad.paste(img, (0, 0))

    #Get the padded image data
    try:
        padded_img_data = pad.tobytes()
    except AttributeError:
        padded_img_data = pad.tostring() # Note: tostring() is deprecated in PIL v3.x

    # Add the overlay with the padded image as the source,
    # but the original image's dimensions
    o_id = camera.add_overlay(padded_img_data, size=img.size)
    o_id.layer = layer

    if duration > 0:
        sleep(duration)
        camera.remove_overlay(o_id)
        o_id = -1 # '-1' indicates there is no overlay

    return o_id # if we have an overlay (o_id > 0), we will need to remove it later


def take_picture():
    for x in range(prep_delay, 0 , -1):
        camera.annotate_text = ("      " + str(x) )
        print("picture in" + str( x))
        sleep(1)
    filename = get_filename()
    camera.annotate_text = ""
    camera.capture(filename)
    print("took a picture")
    if(twitter_enabled):
        ready_for_tweet(filename)
    else:
        overlay_image(filename, 5, 3)

    sleep(1)

def tweet(filename):
    twitter.update_with_media(filename, 'test')

def ready_for_tweet(filename):
   # camera.annotate_text = "Do you want to tweet the picture? Press the green button for yes and the red Button to cancel"
    print("Do you want to tweet the picture?")
    image = './tweet.png'
    image_overlay = overlay_image(filename, 0, 3)
    tweet_text = overlay_image(image, 0 , 4)
    while True:
        input_state_confirm = GPIO.input(pin_confirm_btn)
        input_state_cancel = GPIO.input(pin_cancel_btn)
        if input_state_confirm == False:
            sleep(debounce)
            if input_state_confirm == False:
                print("tweeting")
                tweet(filename)
                remove_overlay(image_overlay)
                remove_overlay(tweet_text)
                camera.annotate_text = "tweeted successfully!"
                sleep(1)
                camera.annotate_text = ""
                break
        elif input_state_cancel == False:
            sleep(debounce)
            if input_state_cancel == False:
                print("cancelled tweeting")
                remove_overlay(tweet_text)
                image_overlay('./cancel_tweet.png', 4, 4)
#                camera.annotate_text = "Did not tweet"
#                sleep(1)
                remove_overlay(image_overlay)
                camera.annotate_text = ""
                break
        sleep(0.05)
    print("finished ready for tweet")

def main():
    print("startup")
    camera.start_preview(resolution=(screen_w,screen_h))
#    camera.zoom = (0.0, 0.0, 2.0, 2.0)
#    camera.annotate_text = "Press the bottom red Button to take a picture!"
    print("press the button to take a photo")
    image = "./take_picture.png"
    pressed = False
    overlay = 0
    while True:
        if(overlay == 0):
            overlay = overlay_image(image, 0, 3)
        input_state = GPIO.input(pin_camera_btn)
        if input_state == False:
            sleep(debounce)
            if input_state == False:
                pressed = True
        sleep(0.05)
        if(pressed):
            camera.annotate_text = ""
            remove_overlay(overlay)
            take_picture()
            pressed = False
            overlay = overlay_image(image, 0, 4)


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
