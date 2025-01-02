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
    youtubeClient = authyt(s3Client)

    print("Uploading video to YouTube")
    videoUploadResponse = uploadVideoRequest(youtubeClient, clippedVideo, bucketKey)
    videoId = videoUploadResponse.get("id")
    print("Uploaded video: ", videoUploadResponse)

    print("Updating playlist")
    uploadPlaylistResponse = uploadPlaylistRequest(youtubeClient, videoId)
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

def uploadVideoRequest(youtubeClient, clippedVideo, bucketKey):
    strippedMatchTitle = Path(bucketKey).stem
    if 'M' in strippedMatchTitle:
        formattedMatchTitle = strippedMatchTitle.replace("M", "Playoff Match ")
    elif 'Q' in strippedMatchTitle:
        formattedMatchTitle = strippedMatchTitle.replace("Q", "Qualification Match ")
    else:
        formattedMatchTitle = strippedMatchTitle
    title = DEFAULT_TITLE if os.environ.get("EVENT_NAME") is None or os.environ.get("EVENT_TYPE") is None or os.environ.get("SEASON_NAME") is None \
        else '{0} {1} - {2} - {3}'.format(os.environ.get("EVENT_NAME"), os.environ.get("EVENT_TYPE"), formattedMatchTitle, os.environ.get("SEASON_NAME"))
    description = DEFAULT_DESCRIPTION if os.environ.get("EVENT_DESCRIPTION") is None else os.environ.get('EVENT_DESCRIPTION')
    request = youtubeClient.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "28",
            "description": description,
            "title": title,
          },
          "status": {
            "privacyStatus": "unlisted"
          }
        },
        media_body=MediaIoBaseUpload(clippedVideo, mimetype="video/mp4")
    )
    return request.execute()

def uploadPlaylistRequest(youtubeClient, videoId):
    playlist = DEFAULT_PLAYLIST if os.environ.get("EVENT_PLAYLIST") is None else os.environ.get("EVENT_PLAYLIST")
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