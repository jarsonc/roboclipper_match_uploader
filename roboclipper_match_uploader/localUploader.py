import os
import time
import googleapiclient.discovery
import googleapiclient.errors

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from util.constants import *

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

matchNum = 0

def callYoutubeWithLocalVideo(fileName):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    youtube = authyt()
    global matchNum
    matchNum += 1

    title = "Qualification Match " + str(matchNum) + " - Edison Division sponsored by Google.org"
    description = "FTC INTO THE DEEP World Championship. \nLive match scores and rankings available at https://ftc-events.firstinspires.org/2024/FTCCMP1"
    request = youtube.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "28",
            "description": description,
            "title": title,
          },
          "status": {
            "privacyStatus": "private"
          }
        },
        media_body=MediaFileUpload(fileName)
    )
    response = request.execute()
    print(response)
    playlistRequest = youtube.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": "PLoRnKfyWNUlcuiB64Ybl7bG8newLU2KKs",
            "resourceId": {
                "kind": "youtube#video",
                "videoId": response.get("id")
            }
          }
        }
    )
    playlistResponse = playlistRequest.execute()
    print(playlistResponse)

def authyt():
    creds = None
    api_service_name = "youtube"
    api_version = "v3"
    clientSecretsFile = "util/desktopSecret.json"
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

class ExampleHandler(FileSystemEventHandler):
    def on_created(self, event): # when file is created
        # do something, eg. call your function to process the image
        try:
            while os.path.getsize(event.src_path) == 0:
                time.sleep(1)
            print("Video detected at %s", event.src_path)
            callYoutubeWithLocalVideo(event.src_path)
            print("Finished Upload")

        except Exception as err:
            print(err)

observer = Observer()
event_handler = ExampleHandler() # create event handler
# set observer to use created handler in directory
observer.schedule(event_handler, path='/Users/jasoncheng/Movies')
observer.start()

# sleep until keyboard interrupt, then stop + rejoin the observer
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
