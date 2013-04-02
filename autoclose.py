import json, os, requests, ConfigParser
from optparse import OptionParser

# Look for our config file
config_file = os.path.dirname(os.path.realpath(__file__)) + '/config'

# If we cant find the config bail out otherwise load our credentials
if (not os.path.isfile(config_file)):
    print "Config file does not exist. Exiting."
    exit()
else:
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    zenoss_location = config.get('zenoss','location')
    zenoss_user = config.get('zenoss','user')
    zenoss_password = config.get('zenoss','password')
    pagerduty_domain = config.get('pagerduty','domain')
    pagerduty_service = config.get('pagerduty','service')
    pagerduty_token = config.get('pagerduty','token')

ROUTERS = { 'EventsRouter': 'evconsole'}

class Zenoss():

    def __init__(self):

        # Create session so we pass our auth cookie along and stay logged in
        self.session = requests.Session()
        self.reqCount = 1

        url = zenoss_location + '/zport/acl_users/cookieAuthHelper/login'
        payload = {'__ac_name': zenoss_user,
                   '__ac_password': zenoss_password,
                   'submitted': True,
                   'came_from': zenoss_location + '/zport/dmd'}

        resp = self.session.post(url, data=payload)

    def _request(self, router, method, data=[]):

        url = zenoss_location + '/zport/dmd/' + ROUTERS[router] + '_router'
        headers = {'content-type': 'application/json; charset=utf-8'}
        payload = {'action': router,
                   'method': method,
                   'data': data,
                   'type': 'rpc',
                   'tid': self.reqCount}

        # Increment our call counter
        self.reqCount += 1

        resp = self.session.post(url, data=json.dumps(payload), headers=headers)

        return resp.json()

    def close_events(self, evids=[]):

        # List of event ids to close
        data = {'evids': evids}

        return self._request('EventsRouter', 'close', [data])['result']

    def get_active_events(self):

        # Defaults we may want to allow to be modified at some point
        data = dict(start = 0, limit = 20)

        # These query params give us severity of critical and error,
        # a state of New or Ack, and a prodState of Production
        data['params'] = { 'severity': ['5', '4'],
                           'eventState': ['0','1'],
                           'prodState': '1000'}

        # Cheasy way to fix broken Zenoss 4 json implementation
        data['keys'] = ['eventState', 'severity', 'component',
                        'firstTime', 'lastTime', 'evid', 'device',
                        'prodState']

        # Query zenoss
        response = self._request('EventsRouter', 'query', [data])['result']

        # Build an array of evids to return
        events = []
        for i in response['events']:
            events.append(i['evid'])

        return events

class Pagerduty():

    def get_resolved_events(self):

        url = 'https://' + pagerduty_domain + '.pagerduty.com/api/v1/incidents'
        payload = {'fields': 'incident_key',
                   'status': 'resolved',
                   'limit': '10',
                   'service': pagerduty_service,
                   'sort_by': 'resolved_on:desc'}

        headers = {'content-type': 'application/json',
                   'Authorization': 'Token token=' + pagerduty_token}

        # Query pagerduty and convert results to json
        response = requests.get(url, data=json.dumps(payload), headers=headers);
        response = response.json()

        # Build an array of incident_keys to return
        incidents = []
        for i in response['incidents']:
            incidents.append(i['incident_key'])

        return incidents

def main():

    # Create a new zenoss object and fetch its events
    zenoss = Zenoss()
    zenoss_events = zenoss.get_active_events()

    # If we have active events lets see if we have resolved them
    # in pagerduty...otherwise we are finished here and there is
    # no need to bother the pagerduty folks
    if zenoss_events:
        pagerduty = Pagerduty()
        pagerduty_events = pagerduty.get_resolved_events()

        # Compare the two sets and see if we have any ids in common
        zenoss_events = set(zenoss_events)
        evids = list(zenoss_events.intersection(pagerduty_events))

        # If we have any matches someone has resoloved the event(s)
        # in pagerduty so lets close them in zenoss
        if evids:
            zenoss.close_events(evids)

if __name__ == "__main__":
    main()