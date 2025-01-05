import json
import os

from app import lambda_handler

with open('../events/exampleSNS.json') as f:
    testEvent = json.load(f)
lambda_handler(testEvent, "")