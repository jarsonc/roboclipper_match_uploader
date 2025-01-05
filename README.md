# roboclipper_match_uploader_sam

Quick and dirty uploader for S3 files received from roboclipper. Works in combination with roboclipper (https://github.com/timtim17/roboclipper-ftc-web) to publish cut videos to YouTube.

Note: Uploaded account needs to be audited by Google as default API limit is likely too low (8 videos / day).

Deploys on uload to AWS account `831866741626`

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command. Inovke with some .json from the events file.

```bash
roboclipper_match_uploader_sam$ sam build --use-container
```

```bash
sam build --use-container && sam local invoke RoboclipperMatchUploaderFunction -e events/testPullWuM10.json
```


