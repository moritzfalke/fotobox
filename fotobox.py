
import configparser
import os
from datetime import datetime
from subprocess import call
from sys import exit as sys_exit
from time import sleep

import RPi.GPIO as GPIO
import picamera
import tweepy
from PIL import Image
from tweepy import TweepError

import counter

try:
    import httplib
except:
    import http.client as httplib

REAL_PATH = os.path.dirname(os.path.realpath(__file__))

# Setting up counter
counter.createFile()
counter.readData()

# Setup Config
config = configparser.ConfigParser()
config.read('config.ini')
print('read the config')
try:
    pin_camera_btn = int(config['CONFIGURATION']['pin_camera_btn'])
    pin_confirm_btn = int(config['CONFIGURATION']['pin_confirm_btn'])
    pin_cancel_btn = int(config['CONFIGURATION']['pin_cancel_btn'])
    pin_shutdown_btn = int(config['CONFIGURATION']['pin_shutdown_btn'])
    prep_delay = int(config['CONFIGURATION']['prep_delay'])
    photo_w = int(config['CONFIGURATION']['photo_w'])
    photo_h = int(config['CONFIGURATION']['photo_h'])
    screen_w = int(config['CONFIGURATION']['screen_w'])
    screen_h = int(config['CONFIGURATION']['screen_h'])
    zoom_x = float(config['ZOOM']['x'])
    zoom_y = float(config['ZOOM']['y'])
    zoom_w = float(config['ZOOM']['w'])
    zoom_h = float(config['ZOOM']['h'])



# Setup Twitter
    twitter_enabled = (config['TWITTER']['enable'] == 'X')
    if(twitter_enabled):
        hashtags = config['TWITTER']['hashtags'].split(",")
        tweet_texts = config['TWITTER']['tweet_texts'].split(",")
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


if(twitter_enabled):
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        twitter = tweepy.API(auth)
    except TweepError as te:
        print('ERROR: Something went wrong with Twitter, aborting')
        sys_exit()

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_camera_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_confirm_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_cancel_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_shutdown_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Min duration (seconds) button is required to be "pressed in" for.
debounce = 0.02

# Setup Camera

camera = picamera.PiCamera()
#camera.rotation = 270
camera.resolution = (photo_h, photo_w)
camera.hflip = True


def get_filename():
    filename = REAL_PATH + "/pictures/" + str(datetime.now()).split('.')[0]
    filename = filename.replace(' ', '_')
    filename = filename.replace(':', '-')
    filename += ".jpg"
    return filename

def have_internet():
    conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except:
        conn.close()
        return False


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

    # Get the padded image data
    try:
        padded_img_data = pad.tobytes()
    except AttributeError:
        padded_img_data = pad.tostring()  # Note: tostring() is deprecated in PIL v3.x

    # Add the overlay with the padded image as the source,
    # but the original image's dimensions
    o_id = camera.add_overlay(padded_img_data, size=img.size)
    o_id.layer = layer

    if duration > 0:
        sleep(duration)
        camera.remove_overlay(o_id)
        o_id = -1  # '-1' indicates there is no overlay

    # if we have an overlay (o_id > 0), we will need to remove it later
    return o_id


def take_picture():
    for x in range(prep_delay, 0, -1):
        camera.annotate_text = ("      " + str(x))
        print("picture in" + str(x))
        sleep(1)
    filename = get_filename()
    camera.annotate_text = ""
    camera.capture(filename)
    print("took a picture")
    if(twitter_enabled):
        ready_for_tweet(filename)
    else:
        overlay_image(filename, 5, 3)
        try:
            os.remove(filename)
        except OSError:
            pass
    sleep(1)


def tweet(filename):
    if(have_internet()):
        text = get_tweet_text()
        try:
            twitter.update_with_media(filename, text)
            try:
                os.remove(filename)
            except OSError:
                pass
            sleep(1)
        except TweepError as te:
            print('Error while uploading to twitter')


def get_tweet_text():
    tweet_text = ''
    for hashtag in hashtags:
      tweet_text +=  ' #' + hashtag
    tweet_text = tweet_texts[counter.getPictureCount()%len(tweet_texts)] + tweet_text
    return tweet_text


def ready_for_tweet(filename):

    print("Do you want to tweet the picture?")
    image = './tweet.png'
    image_overlay = overlay_image(filename, 0, 3)
    tweet_text = overlay_image(image, 0, 4)
    while True:

        input_state_confirm = GPIO.input(pin_confirm_btn)
        input_state_cancel = GPIO.input(pin_cancel_btn)

        if input_state_confirm == False:
            sleep(debounce)
            if input_state_confirm == False:
                print("tweeting")
                remove_overlay(tweet_text)
                wait_for_tweet = './wait_for_tweet.png'
                o_wait = overlay_image(wait_for_tweet, 0 , 4)
                tweet(filename)
                remove_overlay(o_wait)
                successful_tweet = './successful_tweet.png'
                overlay_image(successful_tweet, 4, 4)
                remove_overlay(image_overlay)
                camera.annotate_text = ""
                counter.increasePictureCount()
                break

        elif input_state_cancel == False:
            sleep(debounce)
            if input_state_cancel == False:
                print("cancelled tweeting")
                remove_overlay(tweet_text)
                cancel_tweet = './cancel_tweet.png'
                try:
                    os.remove(filename)
                except OSError:
                    pass
                sleep(1)
                overlay_image(cancel_tweet, 4, 4)
                remove_overlay(image_overlay)
                camera.annotate_text = ""
                break
    sleep(0.05)
    print("finished ready for tweet")

i = 0
blink_speed = 10

def main():

    print("startup")

    camera.start_preview(resolution=(screen_w, screen_h))
    camera.zoom = (zoom_x, zoom_y, zoom_w, zoom_h)

    print("press the button to take a photo")
    camera.annotate_text = ("Baeume gepflanzt heute: " +
                            str(counter.getPictureCount()))

    image1 = "./take_picture.png"
    image2 = "./take_picture2.png"
    overlay = overlay_image(image1, 0, 3)


    i = 0
    blink_speed = 10

    GPIO.add_event_detect(pin_camera_btn, GPIO.FALLING)
    GPIO.add_event_detect(pin_shutdown_btn, GPIO.FALLING)

    while True:

        camera_btn_pressed = None
        shutdown_btn_pressed = None

        if GPIO.event_detected(pin_camera_btn):
            sleep(debounce)
            if GPIO.input(pin_camera_btn) == 0:
                camera_btn_pressed = True

        if GPIO.event_detected(pin_shutdown_btn):
            sleep(debounce)
            if GPIO.input(pin_shutdown_btn) == 0:
                shutdown_btn_pressed = True

        if shutdown_btn_pressed is not None:
            call("sudo nohup shutdown -h now", shell=True)


        if camera_btn_pressed is None:

            i = i + 1
            if i == blink_speed:
                old_overlay = overlay
                overlay = overlay_image(image2, 0, 3)
                remove_overlay(old_overlay)
            elif i == (2 * blink_speed):
                old_overlay = overlay
                overlay = overlay_image(image1, 0, 3)
                remove_overlay(old_overlay)
                i = 0

            sleep(0.1)
            continue


        print("Button Pressed")

        #Silence GPIO detection
        GPIO.remove_event_detect(pin_camera_btn)
        GPIO.remove_event_detect(pin_shutdown_btn)

        remove_overlay(overlay)
        camera.annotate_text = ""

        take_picture()


        camera.annotate_text = ("Baeume gepflanzt heute: " +
                                str(counter.getPictureCount()))

        overlay = overlay_image(image1, 0, 3)

        GPIO.add_event_detect(pin_camera_btn, GPIO.FALLING)
        GPIO.add_event_detect(pin_shutdown_btn, GPIO.FALLING)
        print("ready to take a picture again!")


try:
    main()
except KeyboardInterrupt:
    print("goodbye")

# except Exception as exception:
#    print("unexpected error: ", str(exception))

finally:
    camera.stop_preview()
    camera.close()
    GPIO.cleanup()