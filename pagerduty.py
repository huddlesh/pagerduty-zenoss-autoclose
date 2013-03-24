import json
import requests
from optparse import OptionParser
from config import pd_domain, pd_service, pd_token

def main():

    url = 'https://' + pd_domain + '.pagerduty.com/api/v1/incidents'
    payload = {'fields': 'incident_key',
               'status': 'resolved',
               'limit': '5',
               'offset': '0',
               'service': pd_service,
               'sort_by': 'resolved_on:desc'}

    headers = {'content-type': 'application/json',
               'Authorization': 'Token token=' + pd_token}

    resp = requests.get(url, data=json.dumps(payload), headers=headers);

    print resp.json()

if __name__ == "__main__":
    main()