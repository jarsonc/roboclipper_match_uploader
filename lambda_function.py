import boto3
import googleapiclient.discovery
import googleapiclient.errors
import json
import os

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

print('Loading function')
s3_client = boto3.client('s3')
notVideoFile = {
    'statusCode': 200,
    'body': json.dumps('Non-video file found!')
}
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def lambda_handler(event, context):
    print(event)
    message = event['Records'][0]['Sns']['Message']
    print(type(message))
    print("From SNS: " + message)
    message = json.loads(message)
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    bucketKey = message["Records"][0]["s3"]["object"]["key"]
    clientSecretsKey = "client_secret_166371321956-v3ssn7qdi34mua5lcoq04941lrh1bpc5.apps.googleusercontent.com.json"

    print(bucketName)
    print(bucketKey)
    if ".mp4" not in bucketKey:
        return notVideoFile
    try:        
        clippedVideo = s3_client.get_object(Bucket=bucketName, Key=bucketKey)
        clientSecretsFile = s3_client.get_object(Bucket=bucketName, Key=clientSecretsKey)
        callYouTube(clippedVideo, clientSecretsFile)
        

    except Exception as err:
        print(err)
        
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def callYouTube():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    youtube = authyt()
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "22",
            "description": "Description of uploaded video.",
            "title": "Test video upload."
          },
          "status": {
            "privacyStatus": "unlisted"
          }
        },
        media_body=MediaFileUpload("FTC_wasnstest_Q2.mp4")
    )
    response = request.execute()

    print(response)

def generateThumbnail(eventName, eventType):
    fin = open("default_template.svg", "rt")
    data = fin.read()
    data = data.replace('Line1', eventName)
    data = data.replace('Line2', eventType)
    fin.close()

    fileName = eventName.replace(" ", "").lower() + "_" + eventType.replace(" ", "").lower()
    fin = open(fileName + ".svg", "wt")
    fin.write(data)
    fin.close()

    renderPM.drawToFile(svg2rlg(fileName+".svg"), fileName+".png", fmt="PNG")

def authyt():
    creds = None
    api_service_name = "youtube"
    api_version = "v3"
    clientSecretsFile = "desktopSecret.json"
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            creds.refresh(Request())
        except RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            print(f'Refresh token expired requesting authorization again: {error}')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(clientSecretsFile, SCOPES)
            creds = flow.run_local_server(port=2837)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=creds)