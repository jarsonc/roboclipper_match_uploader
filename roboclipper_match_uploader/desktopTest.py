import json
import os

from roboclipper_match_uploader.app import lambda_handler

with open('../events/exampleSNS.json') as f:
    testEvent = json.load(f)
os.environ["DEBUSSY"] = "1"
os.environ["EVENT_NAME"] = "WA - Asimov"
os.environ["EVENT_TYPE"] = "Semifinal"
os.environ["EVENT_DESCRIPTION"] = """Event Information: \n
                    FIRST Washington - https://firstwa.org/ \n
                    Official FIRST Data Source - https://ftc-events.firstinspires.org/2024/region/USWA"""
os.environ["EVENT_PLAYLIST"] = "PLoRnKfyWNUleDroiOiFaxPXGPPqZJ8Fvr"
os.environ["SEASON_NAME"] = "Into The Deep"
lambda_handler(testEvent, "")