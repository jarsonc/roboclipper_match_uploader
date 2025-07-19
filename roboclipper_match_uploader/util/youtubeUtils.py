import boto3
import googleapiclient.discovery
import googleapiclient.errors
import json
import os

from util.constants import *

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from pathlib import Path

s3Client = boto3.client('s3')

def callYouTube(clippedVideo, bucketKey):
    jschengYtClient = authyt(s3Client)
    
    with open(EVENT_CONFIGS_FILE) as eventConfigFile:
        allEventConfigs = json.load(eventConfigFile)
        eventCode = bucketKey.split('/')[1].strip().upper()
        print(eventCode)
        if eventCode == "USIACMP":
            divisionCode = bucketKey.split('/')[2].strip().upper()
            if divisionCode == "1":
                eventCode = "USIACMPGOLD"
            else:
                eventCode = "USIACMPBLA"
        eventConfig = allEventConfigs.get(eventCode)


    print("Uploading video to YouTube")
    videoUploadResponse = uploadVideoRequest(jschengYtClient, clippedVideo, bucketKey, eventConfig)
    videoId = videoUploadResponse.get("id")
    print("Uploaded video: ", videoUploadResponse)

    print("Updating playlist on jscheng")
    uploadPlaylistResponse = uploadPlaylistRequest(jschengYtClient, videoId, eventConfig)
    print("Successfully updated playlist: ", uploadPlaylistResponse)

    return

def authyt(s3Client):
    creds = None
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
        print("Prompting login (will fail in Lambda)")
        creds = createTokenFile(creds, DESKTOP_TOKEN_FILE)
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds, cache_discovery=False)

def uploadVideoRequest(youtubeClient, clippedVideo, bucketKey, eventConfig):
    title,description = buildTitleAndDescription(bucketKey, eventConfig)
    privacy = "unlisted" if eventConfig is None or eventConfig.get("EVENT_NAME") == "TEST" else "public"
    request = youtubeClient.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "28",
            "description": description,
            "title": title,
          },
          "status": {
            "privacyStatus": privacy
          }
        },
        media_body=MediaIoBaseUpload(clippedVideo, mimetype="video/mp4")
    )
    
    return request.execute()

def uploadPlaylistRequest(youtubeClient, videoId, eventConfig):
    playlist = DEFAULT_PLAYLIST if eventConfig is None else eventConfig.get("EVENT_PLAYLIST")

    request = youtubeClient.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": playlist,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": videoId
            }
          }
        }
    )

    return request.execute()

def uploadPlaylistRequestCRI(youtubeClient, videoId, eventConfig):
    playlist = eventConfig.get("CRI_EVENT_PLAYLIST")

    request = youtubeClient.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": playlist,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": videoId
            }
          }
        }
    )

    return request.execute()

def createTokenFile(creds, clientSecretsFile):
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(clientSecretsFile, SCOPES)
        creds = flow.run_local_server(port=2837)
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
        s3Client.put_object(Body=creds.to_json(), Bucket=ROBOCLIPPER_RESOURCE_BUCKET_NAME, Key=TOKEN_FILE)
    return creds

def buildTitleAndDescription(bucketKey, eventConfig):
    strippedMatchTitle = Path(bucketKey).stem
    if 'M' in strippedMatchTitle:
        formattedMatchTitle = strippedMatchTitle.replace("M", "Playoff Match ")
    elif 'Q' in strippedMatchTitle:
        formattedMatchTitle = strippedMatchTitle.replace("Q", "Qualification Match ")
    else:
        formattedMatchTitle = strippedMatchTitle
    title = DEFAULT_TITLE if eventConfig is None else '{0} {1} - {2} - {3}'.format(eventConfig.get("EVENT_NAME"), eventConfig.get("EVENT_TYPE"), formattedMatchTitle, eventConfig.get("SEASON_NAME"))
    description = DEFAULT_DESCRIPTION if eventConfig is None else eventConfig.get('EVENT_DESCRIPTION')

    return title, description
