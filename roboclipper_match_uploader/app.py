import boto3
import io
import json

from util.youtubeUtils import callYouTube

s3Client = boto3.client('s3')
notVideoFile = {
    'statusCode': 200,
    'body': json.dumps('Non-video file found!')
}
ROBOCLIPPER_RESOURCE_BUCKET_ARN = "arn:aws:s3:::roboclipper-resources"
SERVICE_ACCOUNT_FILE = "service.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
DEFAULT_TITLE = "NEEDS ATTENTION"
DEFAULT_DESCRIPTION = """Event: \n
                      FIRST Washington - Informationhttps://firstwa.org/ \n
                      Official FIRST Data Source - https://ftc-events.firstinspires.org/2024/region/USWA"""

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
        print("Calling YouTube")
        callYouTube(videoDataStream, bucketKey)
        
    except Exception as err:
        print(err)

    return {
        'statusCode': 200,
        'body': json.dumps("Finished exeuction for file: " + bucketKey)
    }    