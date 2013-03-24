import json
import requests
from optparse import OptionParser
from config import zenoss_location, zenoss_user, zenoss_password

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

    def request(self, data=[]):

        url = zenoss_location + '/zport/dmd/evconsole_router'
        headers = {'content-type': 'application/json; charset=utf-8'}
        payload = {'action': 'EventsRouter',
                   'method': 'query',
                   'data': data,
                   'type': 'rpc',
                   'tid': self.reqCount}

        self.reqCount += 1
        resp = self.session.post(url, data=json.dumps(payload), headers=headers)

        return resp.json()

    def get_events(self, filter={}, sort='severity', dir='DESC'):

        data = dict(start=0, limit=20)
        if sort: data['sort'] = sort
        if dir: data['dir'] = dir

        # Cheasy way to fix broken Zenoss 4 json implementation
        data['keys'] = ['eventState', 'severity', 'component',
                        'firstTime', 'lastTime', 'evid', 'device']
        data['params'] = filter

        return self.request([data])['result']

def main():

    usage = 'python %prog --severity=severity --eventState=eventState  --lastTime=lastTime --firstTime=firstTime --stateChange=stateChange --sort=lastTime --dir=DESC'

    parser = OptionParser(usage)
    parser.add_option("--severity", dest='severity', help='severity comma-separated numeric values eg. --severity=5,4 for Critical and Error')
    parser.add_option("--eventState", dest='eventState', default='0,1', help='eventState comma-separated numberic values eg. --eventState=0,1 for New and Ack')
    parser.add_option("--lastTime", dest='lastTime', help='the last time an event was seen. A range that has a start & end in format --lastTime=\'2013-09-13 09:23:21/2012-/2013-09-14 09:23:21/2012\'')
    parser.add_option("--firstTime", dest='firstTime', help='the first time the event was seen --firstTime=\'2013-09-13 09:23:21\'')
    parser.add_option("--stateChange", dest='stateChange', help='when the event last changed state --stateChange=\'2013-09-13 09:23:21\'')
    parser.add_option("--sort", dest='sort', default='lastTime', help='key to sort on --sort=\'lastTime\'')
    parser.add_option("--dir", dest='dir', default='DESC', help='the direction to sort the results --dir=\'ASC\' or --dir=\'DESC\'')
    (options, args) = parser.parse_args()

    # Option is an object but we need dictionary values
    option_dict = vars(options)
    if option_dict['severity']:
        option_dict['severity'] = option_dict['severity'].split(',')
    if option_dict['eventState']:
        option_dict['eventState'] = option_dict['eventState'].split(',')

    # Present by default, sort and dir need removed as they are not a part of the filter string.
    sort_key = option_dict.pop('sort')
    sort_direction = option_dict.pop('dir')

    # Create a new zenoss object and fetch its events
    zenoss = Zenoss()
    z = zenoss.get_events(filter=option_dict, sort=sort_key, dir=sort_direction)

    for e in z['events']:
        outEvid = e['evid']
        outState=e['eventState']
        outdevice=e['device']['text']
        outseverity=e['severity']
        outfirstTime=e['firstTime']
        outlastTime=e['lastTime']
        print 'Evid: %s ,State: %s, Device: %s, Severity: %s, firstTime: %s, lastTime: %s' % (outEvid, outState, outdevice,
                                           outseverity, outfirstTime,
                                           outlastTime)

if __name__ == "__main__":
    main()