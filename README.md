pagerduty-zenoss-autoclose
==========================

The Problem
-------
Engineers wake up, ack and then resolve issues in pagerduty...then have to go back into zenoss and close the event there as well. The idea for this little script is to auto clear zenoss events that have been resolved in pagerduty

Current State
-----------
In current form it will query open events in zenoss that have a state of Ack or New, a severity of Critical or Error, and a Device State of Production. From pagerduty we query for recently closed incidents from a provided service. When comparing the two lists of ids any match represents an event that has been resolved in pagerduty but not in zenoss and closed.

* Tested working with Zenoss 4.2.0
