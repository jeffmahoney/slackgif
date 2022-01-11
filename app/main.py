#!/usr/bin/python3

import hashlib
import hmac
import os
import sys
import time

from random import randint

from google_images_search import GoogleImagesSearch
from flask import Flask, render_template, request, jsonify, Response
from flask_api import status

app=Flask(__name__)

class SignatureError(ValueError):
    pass

try:
    gis_api_key = os.environ['GIS_API_KEY']
except KeyError:
    print("GIS_API_KEY unspecified.  Cannot initialize GoogleImagesSearch.", file=sys.stderr)
    sys.exit(1)

try:
    gis_proj_cx = os.environ['GIS_PROGSEARCH_ENGINE_ID']
except KeyError:
    print("GIS_PROGSEARCH_ENGINE_ID unspecified.  Cannot initialize GoogleImagesSearch.", file=sys.stderr)
    sys.exit(1)

gis = GoogleImagesSearch(gis_api_key, gis_proj_cx, validate_images=False)

try:
    secrets = {}
    hmac_keys = os.environ['SLACK_SIGNING_SECRETS']
    for descr in hmac_keys.split(';'):
        s = descr.split(':')
        if len(s) == 2:
            app_id = s[0]
            key = s[1]
        else:
            app_id = '_default_'
            key = s[0]

        secrets[app_id] = bytes(key, 'utf-8')
    app.config['SIGNING_SECRETS'] = secrets
    app.config['PERFORM_SIGNING'] = True
except KeyError as e:
    print("SLACK_SIGNING_SECRETS unspecified.  Cannot guarantee authenticity.", file=sys.stderr)
    app.config['PERFORM_SIGNING'] = False

def verify_request(request):
    if not app.config['PERFORM_SIGNING']:
        return

    if request.method == 'POST' and request.content_length > 100 * 1024:
        raise SignatureError(f"Request too long: {request.content_length} bytes.")

    request_body = request.get_data().decode()

    if request.method == 'GET':
        qv = request.args
    else:
        qv = request.form

    app_id = qv['api_app_id']

    signing_secrets = app.config['SIGNING_SECRETS']
    try:
        slack_signing_secret = signing_secrets[app_id]
    except KeyError:
        try:
            slack_signing_secret = signing_secrets['_default_']
        except KeyError:
            raise SignatureError(f"No signing secret for app id {app_id} found.")

    slack_request_timestamp = request.headers["X-Slack-Request-Timestamp"]
    slack_signature = request.headers["X-Slack-Signature"]

    # Check that the request is no more than 60 seconds old
    if (int(time.time()) - int(slack_request_timestamp)) > 60:
        raise SignatureError("Verification failed. Request is out of date.")

    # Create a basestring by concatenating the version, the request
    # timestamp, and the request body
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode("utf-8")

    # Hash the basestring using your signing secret, take the hex digest,
    # and prefix with the version number
    my_signature = (
        "v0=" + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()
    )

    # Compare the resulting signature with the signature on the request to verify the request
    if hmac.compare_digest(my_signature, slack_signature) is False:
        raise SignatureError("Verification failed. Signature invalid.")

def get_image(querystring, count):
    _search_params = {
        'q' : querystring,
        'num': count,
        'safe': 'medium',
        'fileType': 'gif',
        'imgType': 'animated',
    }

    # this will only search for images:
    gis.search(search_params=_search_params)

    results = gis.results()

    if count > 1:
        index = randint(0, len(results) - 1)
    else:
        index = 0

    return results[index].url

@app.route('/')
def home():
    try:
        verify_request(request)
    except SignatureError as e:
        return Response(str(e), status.HTTP_403_FORBIDDEN)
    return render_template('index.html')

@app.route('/slackgif', methods=['GET', 'POST'])
def slackgif():
    try:
        verify_request(request)
    except SignatureError as e:
        return Response(str(e), status.HTTP_403_FORBIDDEN)

    try:
        if request.method == 'GET':
            qv = request.args
        else:
            qv = request.form

        text = qv['text']

        cmd = qv['command']
        if cmd == "/newgif" or cmd == "/gif":
            count = 1
        else:
            count = 5
        url = get_image(text, count)

        result = {
                "response_type": "in_channel",
                'text' : f'{cmd} {text}',
                'attachments' : [ { 'image_url' : url }, ],
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({'text' : str(e) })

@app.route('/giftest', methods=['GET', 'POST'])
def giftest():
    try:
        verify_request(request)
    except SignatureError as e:
        return Response(str(e), status.HTTP_403_FORBIDDEN)
    try:
        if request.method == 'GET':
            qv = request.args
        else:
            qv = request.form

        cmd = qv['command']
        text = qv['text']
        result = {
                'text' : f'{cmd} {text}',
                'attachments' : [ { 'text' : str(qv) }, {'text' : str(request.headers) }, ],
                }
        return jsonify(result)
    except Exception as e:
        return jsonify({'text' : str(e) })

if __name__==('__main__'):
    app.run(debug=False, host='0.0.0.0:5001')

