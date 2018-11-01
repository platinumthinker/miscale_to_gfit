import json
import httplib2
from apiclient.discovery import build
 
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from read_weight_csv import read_weights_csv_with_gfit_format
from googleapiclient.errors import HttpError

# Setup for Google API:
# Steps: 
# 1. Go https://console.developers.google.com/apis/credentials
# 2. Create credentials => OAuth Client ID
# 3. Set Redirect URI to your URL or the playground https://developers.google.com/oauthplayground
CLIENT_ID = 'SETUP_AS_ABOVE'
CLIENT_SECRET = 'SETUP_AS_ABOVE'
 
# Redirect URI to google Fit, See Steps 3 above
REDIRECT_URI='https://developers.google.com/oauthplayground'

# See scope here: https://developers.google.com/fit/rest/v1/authorization
SCOPE = 'https://www.googleapis.com/auth/fitness.body.write'

# API Key
# Steps: 
# 1. Go https://console.developers.google.com/apis/credentials
# 2. Create credentials => API Key => Server Key
API_KEY = 'SETUP_AS_ABOVE'

def import_weight_to_gfit():
    # first step of auth
    # only approved IP is my Digital Ocean Server
    flow = OAuth2WebServerFlow(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope=SCOPE, redirect_uri=REDIRECT_URI)
    auth_uri = flow.step1_get_authorize_url()
    print "Copy this url to web browser for authorization: "
    print auth_uri

    # hmm, had to manually pull this as part of a Google Security measure. 
    # there must be a way to programatically get this, but this exercise doesn't need it ... yet...
    token = raw_input("Copy the token from URL and input here: ")
    cred = flow.step2_exchange(token)
    http = httplib2.Http()
    http = cred.authorize(http)
    fitness_service = build('fitness','v1', http=http, developerKey=API_KEY)

    # init the fitness objects
    fitusr = fitness_service.users()
    fitdatasrc = fitusr.dataSources()

    data_source = dict(
	type='raw',
	application=dict(name='maweightimport'),
	dataType=dict(
	  name='com.google.weight',
	  field=[dict(format='floatPoint', name='weight')]
	),
	device=dict(
	  type='scale',
	  manufacturer='unknown',
	  model='unknown',
	  uid='maweightimport',
	  version='1.0',
	)
      )

    def get_data_source_id(dataSource):
      return ':'.join((
	dataSource['type'],
	dataSource['dataType']['name'],
	dataSource['device']['manufacturer'],
	dataSource['device']['model'],
	dataSource['device']['uid']))

    data_source_id = get_data_source_id(data_source)
    # Ensure datasource exists for the device.
    try:
	fitness_service.users().dataSources().get(
	    userId='me',
	    dataSourceId=data_source_id).execute()
    except HttpError, error:
	if not 'DataSourceId not found' in str(error):
	    raise error
	# Doesn't exist, so create it.
	fitness_service.users().dataSources().create(
	    userId='me',
	    body=data_source).execute()

    weights = read_weights_csv_with_gfit_format()
    min_log_ns = weights[0]["startTimeNanos"]
    max_log_ns = weights[-1]["startTimeNanos"]
    dataset_id = '%s-%s' % (min_log_ns, max_log_ns)

    # patch data to google fit
    fitness_service.users().dataSources().datasets().patch(
      userId='me',
      dataSourceId=data_source_id,
      datasetId=dataset_id,
      body=dict(
	dataSourceId=data_source_id,
	maxEndTimeNs=max_log_ns,
	minStartTimeNs=min_log_ns,
	point=weights,
      )).execute()

    # read data to verify
    print fitness_service.users().dataSources().datasets().get(
	userId='me',
	dataSourceId=data_source_id,
	datasetId=dataset_id).execute()

if __name__=="__main__":
import_weight_to_gfit()

