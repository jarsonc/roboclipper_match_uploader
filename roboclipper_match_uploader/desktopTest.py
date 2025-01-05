import json
import os

from app import lambda_handler

with open('../events/testPullWuM10.json') as f:
    testEvent = json.load(f)
lambda_handler(testEvent, "")