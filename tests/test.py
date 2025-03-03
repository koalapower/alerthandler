### test alert for test responses ###
import yaml
from responder import Responder


def main():
    # test alert
    alert = {
        'id': '00000000-0000-0000-0000-000000000030',
        'tenantID': '00000000-0000-0000-0000-000000000001',
        'tenantName': 'Main',
        'name': 'Мой алерт',
        'correlationRuleID': '00000000-0000-0000-0000-000000000002',
        'priority': 'low',
        'status': 'new',
        'firstSeen': '2024-02-16T17:47:08Z',
        'lastSeen': '2024-07-07T17:59:58Z',
        'assignee': '',
        'closingReason': '',
        'overflow': False,
        'events': [],
        'affectedAssets': [],
        'affectedAccounts': []
    }
    # all possible notifications
    notification_types = [
        'new',
        'updated',
        'closed',
        'escalated',
        'assigned',
        'unassigned'
    ]
    # config file
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    myresp = Responder(config)
    # send all response types
    for nt in notification_types:
        print(str(myresp.response(alert, nt)))

if __name__ == '__main__':
    main()
