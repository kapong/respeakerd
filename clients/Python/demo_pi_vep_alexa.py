# -*- coding: utf-8 -*-

import os
import time
import logging
import signal
import threading
from respeakerd_source import RespeakerdSource
from respeakerd_volume_ctl import VolumeCtl
from avs.alexa import Alexa
import sys
from gpiozero import LED

def main():
    logging.basicConfig(level=logging.DEBUG)
    #logging.getLogger('avs.alexa').setLevel(logging.INFO)
    logging.getLogger('hpack.hpack').setLevel(logging.INFO)

    if os.geteuid() != 0 :
        time.sleep(1)

    src = RespeakerdSource()
    alexa = Alexa()
    ctl = VolumeCtl()
    led = LED(12)
    led.on()
    src.link(alexa)

    state = 'thinking'
    last_dir = 0

    def on_ready():
        global state
        print("===== on_ready =====\r\n")
        state = 'off'
        src.on_cloud_ready()

    def on_listening():
        global state
        global last_dir
        print("===== on_listening =====\r\n")
        if state != 'detected':
            print('The last dir is {}'.format(last_dir))
        state = 'listening'

    def on_speaking():
        global state
        print("===== on_speaking =====\r\n")
        state = 'speaking'
        src.on_speak()

    def on_thinking():
        global state
        print("===== on_thinking =====\r\n")
        state = 'thinking'
        src.stop_capture()

    def on_off():
        global state
        print("===== on_off =====\r\n")
        state = 'off'
        led.on()

    def on_detected(dir, index):
        global state
        global last_dir
        logging.info('detected hotword:{} at {}`'.format(index, dir))
        state = 'detected'
        last_dir = (dir + 360 - 60)%360
        alexa.listen()
        led.off()

    def on_vad():
        # when someone is talking
        # print("."),
        # sys.stdout.flush()
        pass

    def on_silence():
        # when it is silent 
        pass

    alexa.state_listener.on_listening = on_listening
    alexa.state_listener.on_thinking = on_thinking
    alexa.state_listener.on_speaking = on_speaking
    alexa.state_listener.on_finished = on_off
    alexa.state_listener.on_ready = on_ready
   
    alexa.Speaker.CallbackSetVolume(ctl.setVolume)
    alexa.Speaker.CallbackGetVolume(ctl.getVolume)
    alexa.Speaker.CallbackSetMute(ctl.setMute)

    src.set_callback(on_detected)
    src.set_vad_callback(on_vad)
    src.set_silence_callback(on_silence)

    src.recursive_start()

    is_quit = threading.Event()
    def signal_handler(signal, frame):
        print('Quit')
        is_quit.set()

    signal.signal(signal.SIGINT, signal_handler)

    while not is_quit.is_set():
        try:
            time.sleep(1)
        except SyntaxError:
            pass
        except NameError:
            pass

    src.recursive_stop()


if __name__ == '__main__':
    main()






