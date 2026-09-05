import requests
import json
from elevenlabs.client import ElevenLabs
# Create an account on https://www.texttovoice.online and take your userId
# Alternatively this can be found as part of the request made when generating audio
USER_ID = "<User_ID>"
def text_to_voice_online(text):
    """
    API endpoint and request formatting taken from texttovoice to let the app make requests directly to their audio generation endpoint.
    This means it is not an official endpoint and this request is susceptible to changes made by texttovoice.
    """
    url = "https://www.texttovoice.online/"
    data = {
        "ttv_mode": "1",
        "bgMusic": "undefined",
        "userID": "<User_ID>",
        "provider": "aws",
        "text": text,
        "voice": "Zhiyu",
        "language": "cmn-CN",
        "speed": "100",
        "volume": "3",
        "exaggeration": "undefined",
        "usePremium": "0",
        "premium": "0",
        "voiceStyle": "neutral",
        "isEmotion": "0",
        "vol": "0.3",
        "rand": "20",
        "isSample": "0",
        "useSSML": "0",
        "voiceName": "Zhiyu",
        "isGem": "0",
        "speechPrompt": "undefined"
    }

    res_loc = requests.post(url + "scripts/awsRequest2.php", data=data)
    file_loc = json.loads(res_loc.content)["content"]

    res = requests.get(url + file_loc)
    return res.content

# Follow the instructions at https://elevenlabs.io/app/developers/api-key and https://elevenlabs.io/app/voice-lab to populate the values below
ELL_VOICE_ID = "<VOICE_ID>"
ELL_API_KEY = "<API_KEY>"

def text_to_voice_elevenlabs(text):
    client = ElevenLabs(api_key=ELL_API_KEY)
    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id=ELL_VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    return b"".join(audio_stream)
