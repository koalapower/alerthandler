#!/bin/bash

mkdir /opt/alerthandler/
mkdir /opt/alerthandler/db/
mkdir /opt/alerthandler/certs/
mkdir /opt/alertmanager/

tar -xvf $1 --one-top-level=/opt/alertmanager/ --strip-components=1

python3 -m pip install -r requirements.txt

cp src/* /opt/alerthadler/
PYTHON="$(which python3)"
sed -i "s|python3|$PYTHON|g" templates/alerthandler/alerthandler.service
cp templates/alerthandler/config.yml /opt/alerthandler/
cp templates/alerthandler/alerthandler.service /etc/systemd/system/

cp templates/alertmanager/alertmanager.yml /opt/alertmanager/
cp templates/alertmanager/email.tmpl /opt/alertmanager/
cp templates/alertmanager/alertmanager.service /etc/systemd/system/

useradd -Mrs /usr/bin/false alerthandler
useradd -Mrs /usr/bin/false alertmanager

chown -R alertmanager:alertmanager /opt/alertmanager
chown -R alerthandler:alerthandler /opt/alerthandler
