import io
import boto3
from cachetools import Cache
import googleapiclient.discovery
import googleapiclient.errors
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

s3Client = boto3.client('s3')
notVideoFile = {
    'statusCode': 200,
    'body': json.dumps('Non-video file found!')
}
ROBOCLIPPER_RESOURCE_BUCKET_ARN = "arn:aws:s3:::roboclipper-resources"
SERVICE_ACCOUNT_FILE = "service.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
DEFAULT_DESCRIPTION = "Test!"
DEFAULT_TITLE = "NEEDS ATTENTION"
# DEFAULT_DESCRIPTION = """Event: \n
#                       FIRST Washington - Informationhttps://firstwa.org/ \n
#                       Official FIRST Data Source - https://ftc-events.firstinspires.org/2024/region/USWA"""

def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    message = json.loads(message)
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    bucketKey = message["Records"][0]["s3"]["object"]["key"]

    print("Bucket Name from SNS: " + bucketName)
    print("Bucket Key from SNS: " + bucketKey)
    if ".mp4" not in bucketKey:
        return notVideoFile
    try:
        videoDataStream = io.BytesIO()
        print("Downloading file from S3")
        s3Client.download_fileobj(bucketName, bucketKey, videoDataStream)
        print("Finished download")
        response = callYouTube(videoDataStream, bucketKey)
        
    except Exception as err:
        print(err)

    return {
        'statusCode': 200,
        'body': json.dumps("Sucessfully uploaded video: {0} at YouTube link: https://youtu.be/{1}".format(bucketKey, response.get("id")))
    }
        

def callYouTube(clippedVideo, bucketKey):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    youtube = authyt()
    formattedMatchTitle = Path(bucketKey).stem
    title = DEFAULT_TITLE if os.environ.get("EVENT_NAME") is None or os.environ.get("EVENT_TYPE") is None or os.environ.get("SEASON_NAME") is None else '{0} - {1} - {2} - {3}'.format(os.environ.get("EVENT_NAME"), os.environ.get("EVENT_TYPE"), formattedMatchTitle, os.environ.get("SEASON_NAME"))
    description = DEFAULT_DESCRIPTION if os.environ.get("EVENT_DESCRIPTION") is None else os.environ['EVENT_DESCRIPTION']
    request = youtube.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "28",
            "description": description,
            "title": title
          },
          "status": {
            "privacyStatus": "unlisted"
          }
        },
        media_body=MediaIoBaseUpload(clippedVideo, mimetype="video/mp4")
    )
    print("Uploading video to YouTube")
    response = request.execute()
    print("Video upload completed")
    
    return response

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
    if os.path.exists(TOKEN_FILE):
        try:
            print("Trying to refresh creds")
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            creds.refresh(Request())
        except RefreshError as error:
            creds = None
            print(f'Refresh token expired requesting authorization again: {error}')
    else:
        try:
            tokenFileFromS3 = s3Client.get_object(Bucket="roboclipper-resources", Key=TOKEN_FILE)     
            credJson = json.loads(tokenFileFromS3["Body"].read().decode())
            creds = Credentials.from_authorized_user_info(credJson, SCOPES)
            creds.refresh(Request())
        except Exception as err:
            creds = None
            print(f'Error while fetching from S3: {err}')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(clientSecretsFile, SCOPES)
            creds = flow.run_local_server(port=2837)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            s3Client.put_object(Body=creds.to_json, Bucket=ROBOCLIPPER_RESOURCE_BUCKET_ARN, Key=TOKEN_FILE)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=creds, cache_discovery=False)

# with open('../events/exampleSNS.json') as f:
#     testEvent = json.load(f)
# lambda_handler(testEvent, "")