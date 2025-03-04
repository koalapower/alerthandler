import sqlite3
import time
import signal
import argparse
import yaml
import kuma_api
import responder
import logging
import os


class SignalHandler:
    shutdown_requested = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, *args):
        print('Request to shutdown received, stopping')
        self.shutdown_requested = True

    def can_run(self):
        return not self.shutdown_requested


def select_alert_ids(db):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.row_factory = lambda c, row: row[0]
        ids = cursor.execute('''SELECT alert_id FROM Alerts''').fetchall()
        cursor.close()
        conn.commit()
    return ids


def select_whole_alert(db, alert_id):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        whole_alert = cursor.execute(
            '''SELECT alert_status, alert_assignee, last_seen FROM Alerts WHERE alert_id = ?''', (alert_id,)).fetchone()
        cursor.close()
        conn.commit()
    return whole_alert


def update_alert(db, alert_tbu, upd_type):
    if upd_type == 'last_seen':
        update_alert_time(db, alert_tbu['id'], alert_tbu['lastSeen'])
    elif upd_type == 'assignee':
        update_alert_assignee(db, alert_tbu['id'], alert_tbu['assignee'])
    elif upd_type == 'alert_status':
        update_alert_status(db, alert_tbu['id'], alert_tbu['status'])


def update_alert_status(db, alert_id, status):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE Alerts SET alert_status = ? WHERE alert_id = ?''', (status, alert_id,))
        cursor.close()
        conn.commit()


def update_alert_assignee(db, alert_id, assignee):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE Alerts SET alert_assignee = ? WHERE alert_id = ?''', (assignee, alert_id,))
        cursor.close()
        conn.commit()


def update_alert_time(db, alert_id, _time):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE Alerts SET last_seen = ? WHERE alert_id = ?''', (_time, alert_id,))
        cursor.close()
        conn.commit()


def delete_alert(db, alert_id):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM Alerts WHERE alert_id = ?''', (alert_id,))
        cursor.close()
        conn.commit()


def insert_new_alert(db, alert):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Alerts (
                     alert_id, alert_name, alert_status, alert_assignee,
                     first_seen, last_seen,
                     tenant
                     ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (alert['id'], alert['name'], alert['status'], alert['assignee'],
                        alert['firstSeen'], alert['lastSeen'],
                        alert['tenantID']))
        cursor.close()
        conn.commit()

### can be replaced by your own method to check response from responder
def check_status(status, response, alert_id):
    if status == responder.OK:
        logging.info(f"Alert with id {alert_id} successfully sent")
    else:
        logging.error(f"Error while sending alert with id {alert_id}: {response}")
###

def main():
    
    log_handler = logging.FileHandler(filename='/opt/alerthandler/alerthandler.log', encoding='utf_8')
    logging.basicConfig(handlers=[log_handler], level=logging.INFO, format="%(asctime)s;%(levelname)s;%(message)s")
    logging.info("Alerthandler started")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config file', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml'))
    args = parser.parse_args()
    config_path = args.config
    
    logging.info(f"Using config {config_path}")
    # config load
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    addr = config['kuma']['address']
    api_port = config['kuma']['port']
    token = config['kuma']['token']
    ca = config['kuma']['ca']
    db_name = config['db']['path']
    timeout = config['general']['timeout']
    signal_handler = SignalHandler()
    my_kuma = kuma_api.Kuma(address=addr, port=api_port, token=token, ca=ca)
    ### can be replaced by your own responder
    my_responder = responder.Responder(config)
    ###
    while signal_handler.can_run():

        length = 250
        page = 1
        all_alerts = []
        # create DB if not exist
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Alerts (
            id INTEGER PRIMARY KEY,
            alert_id TEXT NOT NULL,
            alert_name TEXT NOT NULL,
            alert_status TEXT NOT NULL,
            alert_assignee TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            tenant TEXT NOT NULL
            )
            ''')
            cursor.close()
            conn.commit()
        # select min last_seen from DB
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            last_seen = cursor.execute('''SELECT last_seen FROM Alerts ORDER BY last_seen ASC''').fetchone()
            cursor.close()
            conn.commit()

        while length == 250:
            if last_seen is not None: # DB contains alerts
                status, response = my_kuma.get_alerts(page=page, _from=last_seen)
                if status == kuma_api.OK:
                    alerts = response
                    logging.debug(f"Fetched {len(alerts)} alerts")
                else:
                    logging.error(f"{response}")
                    break

            else:  # first launch
                logging.info("It's alerthandler's first launch. Try to get all alerts from KUMA.")
                status, response = my_kuma.get_alerts(page=page, status=["new", "assigned", "escalated"],
                                            _from='1970-01-01T00:00:00Z')
                if status == kuma_api.OK:
                    alerts = response
                    logging.info(f"Fetched {len(alerts)} alerts")
                else:
                    logging.error(f"{response}")
                    break

            length = len(alerts)
            if length == 0:
                break  # nothing to do
            all_alerts.extend(alerts)
            page = page + 1

        logging.info(f"Fetched {len(all_alerts)} alerts")

        if last_seen is not None: # DB contains alerts
            ids = select_alert_ids(db_name)
            for alert in all_alerts:
                # alert id not in DB 
                if not alert['id'] in ids:
                    # alert's status isn't closed, so insert alert into DB and send response with status New
                    if alert['status'] != 'closed': 
                        ### can be replaced by your own responder
                        status, response = my_responder.response(alert, 'new_alert')
                        check_status(status, response, alert['id'])
                        ###
                        insert_new_alert(db_name, alert)
                # alert id in DB
                else:
                    alert_in_db = select_whole_alert(db_name, alert['id'])
                    # alert's last_seen time not the same as in DB, so udpate alert into DB and send response with status Updated
                    if alert_in_db[2] != alert['lastSeen']:
                        ### can be replaced by your own responder
                        status, response = my_responder.response(alert, 'updated')
                        check_status(status, response, alert['id'])
                        ###
                        update_alert(db_name, alert, upd_type='last_seen')
                    # alert's assignee not the same as in DB
                    if alert_in_db[1] != alert['assignee']:
                        # alert's assignee now empty, so send response with status unassigned
                        if alert['assignee'] == '':
                            ### can be replaced by your own responder
                            status, response = my_responder.response(alert, 'unassigned')
                            check_status(status, response, alert['id'])
                            ###
                        # alert's assignee not empty, so send response with status assigned
                        else:
                            ### can be replaced by your own responder
                            status, response = my_responder.response(alert, 'assigned')
                            check_status(status, response, alert['id'])
                            ###
                        # udpate alert into DB
                        update_alert(db_name, alert, upd_type='assignee')
                    # alert's status has been changed
                    if alert_in_db[0] != alert['status']:
                        # alert status is closed now, so send response with status Closed and delete alert from DB
                        if alert['status'] == 'closed':
                            ### can be replaced by your own responder
                            status, response = my_responder.response(alert, 'closed')
                            check_status(status, response, alert['id'])
                            ###
                            delete_alert(db_name, alert['id'])
                        # alert status isn't closed, so update alert in DB
                        else:
                            update_alert(db_name, alert, upd_type='alert_status')
                            # alert status is escalated, so send response with status Escalated
                            if alert['status'] == 'escalated':
                                ### can be replaced by your own responder
                                status, response = my_responder.response(alert, 'escalated')
                                check_status(status, response, alert['id'])
                                ###
        
        # for first launch just insert all alerts in DB without any response
        else:  
            for alert in all_alerts:
                insert_new_alert(db_name, alert)
        # sleep for timeout (10s by default)
        time.sleep(timeout)


if __name__ == '__main__':
    main()
