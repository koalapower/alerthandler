import requests
import ssl
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


class Kuma:

    def __init__(self, address, port, token, ca):
        self.session = requests.Session()
        # verify server cert if CA in config
        if ca:
            self.session.mount('https://', SSLAdapter())
        # don't verify and hide warnings
        else:
            self.session.verify = False
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        self.address = address
        self.port = port
        self.token = token
        self.headers = {'Authorization': 'Bearer ' + token}
        self.session.headers.update(self.headers)


    def _make_request(self, method, route, params=None, data=None, files=None, resp_status_code_expected=200, response_type='json'):
        url = 'https://{}:{}/api/v1/{}'.format(self.address, self.port, route)
        try:
            response = self.session.request(
                method, url,
                params=params,
                data=data,
                files=files
            )
            if response.status_code != resp_status_code_expected:
                return ERROR, str(response.status_code) + ": " + str(response.text)
            if response_type == 'json':
                return OK, response.json()
        except Exception as e:
            return ERROR, str(e)


    def make_get_request(self, *args, **kwargs):
        return self._make_request('get', *args, **kwargs)


    def get_alerts(self, page: int = None, id=None, tenantID=None, name=None, timestampField='lastSeen',
                   _from=None, to=None, status=None, withEvents: bool = False, withAffected: bool = False):
        params = {
            "page": page,
            "id": id,
            "tenantID": tenantID,
            "name": name,
            "timestampField": timestampField,
            "from": _from,
            "to": to,
            "status": status,
        }
        if withEvents:
            params['withEvents'] = ""
        if withAffected:
            params['withAffected'] = ""
        return self.make_get_request('alerts/', params)
