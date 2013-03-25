import json
import requests
from optparse import OptionParser
from config import zenoss_location, zenoss_user, zenoss_password, pagerduty_domain, pagerduty_service, pagerduty_token

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

    def _request(self, method, data=[]):

        url = zenoss_location + '/zport/dmd/evconsole_router'
        headers = {'content-type': 'application/json; charset=utf-8'}
        payload = {'action': 'EventsRouter',
                   'method': method,
                   'data': data,
                   'type': 'rpc',
                   'tid': self.reqCount}

        self.reqCount += 1

        resp = self.session.post(url, data=json.dumps(payload), headers=headers)

        return resp.json()

    def close_events(self, evids=[]):

        # List of event ids to close
        data = {'evids': evids}

        return self._request('close', [data])['result']

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

        return self._request('query', [data])['result']

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

        r = requests.get(url, data=json.dumps(payload), headers=headers);
        return r.json()

def main():

    # Create a new zenoss object and fetch its events
    zenoss = Zenoss()
    z = zenoss.get_active_events()

    pagerduty = Pagerduty()
    p = pagerduty.get_resolved_events()

    # Show me my Zenoss events
    print 'Zenoss'
    for e in z['events']:
        print 'Evid = %s, Event State = %s, Device State: %s' % (e['evid'], e['eventState'], e['prodState'])

    # Show me my Pagerduty events
    print 'Pagerduty:'
    for i in p['incidents']:
        print 'incident_key = %s' % (i['incident_key'])



if __name__ == "__main__":
    main()