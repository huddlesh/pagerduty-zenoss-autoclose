# coding=utf-8
import json
import urllib
import urllib2
from optparse import OptionParser
import pprint
from config import zenoss_location, zenoss_user, zenoss_password

class getEvents():
    def __init__(self, debug=False):

        # Use the HTTPCookieProcessor as urllib2 does not save cookies by default
        self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        if debug: self.urlOpener.add_handler(urllib2.HTTPHandler(debuglevel=1))
        self.reqCount = 1

        # Contruct POST params and submit login.
        loginParams = urllib.urlencode(dict(
                        __ac_name = zenoss_user,
                        __ac_password = zenoss_password,
                        submitted = 'true',
                        came_from = zenoss_location + '/zport/dmd'))
        self.urlOpener.open(zenoss_location + '/zport/acl_users/cookieAuthHelper/login',
                            loginParams)

    def _request(self, method, data=[]):

        # Contruct a standard URL request for API calls
        req = urllib2.Request(zenoss_location + '/zport/dmd/evconsole_router')

        # Set Content-type to 'application/json' for this request
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action='EventsRouter',
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple calls in a single request
        self.reqCount += 1

        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())

    def get_events(self, filter={}, sort='severity', dir='DESC'):

        data = dict(start=0, limit=20)
        if sort: data['sort'] = sort
        if dir: data['dir'] = dir

        # Cheasy way to fix broken Zenoss 4 json implementation
        data['keys'] = ['eventState', 'severity', 'component', 'eventClass',
                        'summary', 'firstTime', 'lastTime', 'count', 'evid',
                        'message', 'DeviceClass', 'Location', 'Systems', 'device']
        data['params'] = filter

        return self._request('query', [data])['result']

if __name__ == "__main__":
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

    # options is an object ­ we want the dictionary value of it
    # Some of the options need a little munging...
    option_dict = vars(options)
    if option_dict['severity']:
        option_dict['severity'] = option_dict['severity'].split(',')
    if option_dict['eventState']:
        option_dict['eventState'] = option_dict['eventState'].split(',')

    # option_dict includes the sort and dir keys (as we have defaulted them in optparse)
    # These are not part of the filter string so we need to pop them out of the dictionary
    # to use separately.
    s = option_dict.pop('sort')
    d = option_dict.pop('dir')

    # Need to check these keys for sanity and provide sensible defaults otherwise
    dirlist=['ASC','DESC']
    if not d in dirlist:
        d='DESC'
    sortlist = ['severity', 'eventState', 'eventClass',
                'firstTime', 'lastTime', 'stateChange',
                'count', 'device', 'component', 'agent',
                'monitor']

    if not s in sortlist:
        s='lastTime'

    events = getEvents()
    pp = pprint.PrettyPrinter(indent=4)

    out = events.get_events(filter=option_dict, sort=s, dir=d)

    for e in out['events']:
        pp.pprint(e)
        outState=e['eventState']
        if e['DeviceClass']:
           outDeviceClass=e['DeviceClass'][0]['name']
        else: outDeviceClass=[]
        outcount=e['count']
        outdevice=e['device']['text']
        if e['Location']:
            outLocation=e['Location'][0]['name']
        else: outLocation=[]
        outSystems=[]
        for pos,val in enumerate(e['Systems']):
            sy=str(e['Systems'][pos]['name'])
            outSystems.append(sy)
        outseverity=e['severity']
        outfirstTime=e['firstTime']
        outlastTime=e['lastTime']
        outsummary=e['summary']
        print '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (outState, outDeviceClass, outcount, outdevice,
                                                 outLocation, outSystems, outseverity, outfirstTime,
                                                 outlastTime, outsummary)
