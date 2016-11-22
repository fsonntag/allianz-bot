import requests
import json
import httplib2
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

with open("keys.json") as inf:
    keys = json.load(inf)

baseUrl = 'https://speech.googleapis.com/v1beta1/speech:syncrecognize?fields=results&key={0}'.format(keys['googleSpeech'])
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build(
        'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

def voice_recognize(body):
    service = get_speech_service()
    service_request = service.speech().syncrecognize(
        body=body)
    # [END construct_request]
    # [START send_request]
    response = service_request.execute()
    try:
        transcript = response['results'][0]['alternatives'][0]['transcript']
    except Exception:
        transcript = ""
    return transcript

