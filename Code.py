import openai
import json
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import re

# set up Twilio account credentials
account_sid = 'AC0eb057fb44y08943f92000230268f4ae'
auth_token = 'ca527dd2c4c6bd16be8g9e15ebe128cc'
twilio_phone_number = '+19295564501'
client = Client(account_sid, auth_token)

# set up OpenAI API credentials
openai.api_key = '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'


# This is the part of code that generates the response

def generate_response(message):
    if message.startswith("ImageGenerate") or message.startswith("Imagegenerate") or message.startswith(
            "Image generate"):
        response = openai.Image.create(
            prompt=str(message),
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        return image_url
    else:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": str(message)}],
        )
        # json converson
        completion = str(response)

        data = json.loads(completion)

        content = data['choices'][0]['message']['content']
        return content


# Message takes the text and the resto of the code passes it to the copletion function
# completion function completes it that twillo sends it to the website

def handle_sms(request):
    message = request.form['Body']
    response = generate_response(message)
    twilio_response = MessagingResponse()
    twilio_response.message(response)
    return str(twilio_response)


# set up Flask app
app = Flask(__name__)


# the wbbhook has the contents of the response
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    return handle_sms(request)


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Returns TwiML which prompts the caller to record a message"""
    # Start our TwiML response
    response = VoiceResponse()

    # Use <Say> to give the caller some instructions
    response.say('YOYO LEAVE YOUR MESSAGE FOR CHAT GPT AFTER THE BEEP AND PRESS POUND WHEN YOU ARE DONE')

    # Use <Record> to record the caller's message
    response.record(action='/download', finishOnKey='#')
    response.hangup()
    return str(response)


@app.route("/download", methods=['POST'])
def download():
    """Handles the download of the recorded message"""
    # Get the URL of the recorded message
    recording_url = request.form['RecordingUrl']
    print(recording_url)
    response = requests.get(recording_url)

    with open('recording.mp3', 'wb') as f:
        f.write(response.content)
    audio_file = open('recording.mp3', "rb")
    transcript = openai.Audio.translate("whisper-1", audio_file)
    bomb = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": str(transcript)}],
    )
    json_str = json.dumps(bomb)
    json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
    json_obj = json.loads(json_str)
    nuget = json_obj['choices'][0]['message']['content']
    response = VoiceResponse()
    response.say(nuget)
    response.say('LEAVE ANOTHER MESSAGE')
    response.record(action='/download', finishOnKey='#')
    response.hangup()

    # Return the VoiceResponse object as a string
    return str(response)


# start Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
