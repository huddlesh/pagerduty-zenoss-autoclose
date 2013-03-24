import json
import requests
from optparse import OptionParser
from config import pagerduty_domain, pagerduty_service, pagerduty_token

def main():

    usage = 'python %prog --fields=fields --status=status  --limit=limit --offset=offset --sort_by=sort_by'

    parser = OptionParser(usage)
    parser.add_option("--fields", dest='fields', default='incident_key', help='')
    parser.add_option("--status", dest='status',default='resolved', help='')
    parser.add_option("--limit", dest='limit',default='5', help='')
    parser.add_option("--offset", dest='offset',default='0', help='')
    parser.add_option("--sort_by", dest='sort_by', default='resolved_on:desc', help='')
    (options, args) = parser.parse_args()

    url = 'https://' + pagerduty_domain + '.pagerduty.com/api/v1/incidents'
    payload = {'fields': options.fields,
               'status': options.status,
               'limit': options.limit,
               'offset': options.offset,
               'service': pagerduty_service,
               'sort_by': options.sort_by}

    headers = {'content-type': 'application/json',
               'Authorization': 'Token token=' + pagerduty_token}

    resp = requests.get(url, data=json.dumps(payload), headers=headers);

    print resp.json()

if __name__ == "__main__":
    main()