# openvoc.py
# requires openai and mpv player for Linux
# no player is required for Windows
#    VOICES:
#    'alloy','ash','ballad','coral','echo','fable','nova','onyx','sage','shimmer'
#    EXAMPLE:
#    openvoc.textospeech('nova', 'speech.mp3', 'Hello, this is nova speaking.')
#

import openai
import subprocess
import platform

def play_file(speech_file_path):
    ''' Play the audio file currently set
    different actions occur based on running OS '''
    playcmd = []
    if platform.system() == "Windows":
        playcmd = [speech_file_path,]
    else:
        playcmd = ['mpv', speech_file_path]
    subprocess.Popen(playcmd)

def textospeech(voc, fou, inp):
    ''' create the audio file
        get parameters from GUI
        (response is an mp3 audio file)
        and get response from openai
    '''
    speech_file_path = fou

    try:
        with openai.audio.speech.with_streaming_response.create(
          model="gpt-4o-mini-tts",
          voice=voc,
          response_format="mp3",
          input=inp
        ) as response:
          response.stream_to_file(speech_file_path)
          play_file(speech_file_path)
          return 0  # success
    except Exception as e:
        return 2  # problems
