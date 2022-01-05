# slashgif - GIF slash command for Slack

Simple script to fetch GIFs using Google Image Search

## Overview
This script will act as the target for [Slack](https://slack.com) slash commands. It supports three potential targets:
* `/gif [search terms]` - Will post the first animated GIF found with Google Image Search to the channel in which it was invoked.
* `/randgif [search terms]` - Will post a random animated GIF of the top five found with Google Image Search to the channel in which it was invoked.
* `/giftest [unused]` - Used for debugging. Will send the contents of the HTTP POST request sent to the script as well as any headers privately to the user who invoked it.


It is possible for this script to service more than one Slack workspace. It is recommended to enable signature checking to ensure that only the workspaces intended will be serviced.

## Prerequisites
* Visit https://console.developers.google.com and create a project.
* Visit https://console.developers.google.com/apis/library/customsearch.googleapis.com and enable "Custom Search API" for your project.
* Visit https://console.developers.google.com/apis/credentials and generate API key credentials for your project.
* Visit https://cse.google.com/cse/all and in the web form where you create/edit your custom search engine enable "Image search" option and for "Sites to search" option select "Search the entire web but emphasize included sites".

## Configuration using environment variables
The following environment variables are used to establish the parameters for the Google API and validate request signatures from Slack.
* `GIS_API_KEY`
	* This is mandatory and must contain the API Key configured above.
* `GIS_PROGSEARCH_ENGINE_ID`
	* This is mandatory and must contain the "Search Engine ID" for the Custom Search configured above.
* `SLACK_SIGNING_SECRETS`
	* This is recommended and should contain the contents of the _Signing Secret_ field in the _Basic Information_ page in your app's management page. If this app will be used by more than one workspace, the secrets may be specified by pairing the app API ID and secret separated by a colon (`:`) and separating each pair with a semicolon (`;`) as follows:
		* `SLACK_SIGNING_SECRETS=app_api_id1:secret;app_api_id2:secret2;...`

## Execution
The script as packaged in this repository is implemented as a [Flask](https://flask.palletsprojects.com/en/2.https://flask.palletsprojects.com/en/2.0.x/0.x/) endpoint in a [Docker](https://docker.com) container and orchestrated by [Docker Compose](https://docs.docker.com/compose/). It exposes an HTTP-only endpoint by default and additional configuration is required to enable HTTPS either via Traefik or an external reverse proxy.  Such configuration is beyond the scope of this document.

To create the initial container or when you've changed the script or need to update dependencies:
* `$ docker build -t slackgif .`

To start the orchestrated container once the environment variables above are configured by creating a `.env` file containing the values:
* `$ docker-compose up -d slackgif`

