import datetime
import requests
import json
import ssl

import requests.certs

from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

OK = 'OK'
ERROR = 'ERROR'

### fix for certificate in python issues
class SSLAdapter(HTTPAdapter):   
    
    def __init__(self, ca):
        self.ca = ca
        return super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context(cafile=self.ca)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)
###


class Responder:

    def __init__(self, config):
        
        self.config = config
        self.baseurl = self.config['alertmanager']['baseurl']
        self.session = requests.Session()
        self.session.headers = {'Content-type': 'application/json'}
        # if client cert and key in config use client cert auth
        if self.config['alertmanager']['client_cert'] and self.config['alertmanager']['client_key']:
            self.session.cert = (self.config['alertmanager']['client_cert'], self.config['alertmanager']['client_key'])
        # if server CA cert in config use cert verifying
        if self.config['alertmanager']['server_ca']:
            self.session.mount('https://', SSLAdapter(self.config['alertmanager']['server_ca']))
        # do not verify server cert and do not show warnings
        else:
            self.session.verify = False
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


    # add timezone and convert time
    def prepare_time(self, time: str):
        parsed_time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        tz = self.config['general']['timezone']
        parsed_tz = datetime.datetime.strptime(tz[1:], '%H%M')
        delta = datetime.timedelta(hours=parsed_tz.hour, minutes=parsed_tz.minute)
        if tz[:1] == '+':
            prepared_time = parsed_time + delta
        else:
            prepared_time = parsed_time - delta
        return str(prepared_time) + ' ' + tz


    # convert alert into alertmanager format
    def prepare_message(self, notification_type: str, alert: dict):
        message = [{"labels": {
            "alert_id": alert['id'],
            "tenant_id": alert['tenantID'],
            "tenant_name": alert['tenantName'],
            "alert_name": alert['name'],
            "rule_id": alert['correlationRuleID'],
            "alert_priority": alert['priority'],
            "alert_status": alert['status'],
            "first_seen": self.prepare_time(alert['firstSeen']),
            "last_seen": self.prepare_time(alert['lastSeen']),
            "alert_assignee": alert['assignee'],
            "closing_reason": alert['closingReason'],
            "alert_overflow": str(alert['overflow']),
            # array to string because of alermanager limitations
            "alert_assets": str(alert['affectedAssets']),
            # array to string because of alermanager limitations
            "alert_accounts": str(alert['affectedAccounts']),
            "notification_type": notification_type,
            "KUMA_URL": "https://" + self.config['kuma']['address'] + ":7220/alerts/" + alert['id']
        }}]
        return message


    def response(self, alert: dict, notification_type: str): 
        message = self.prepare_message(notification_type, alert)
        
        try:
            response = self.session.request(method='POST', url=self.baseurl + '/alerts', data=json.dumps(message))
            if response.status_code == 200:
                return OK, response.text
            else:
                return ERROR, response.text
        except Exception as e: 
            return ERROR, str(e)
