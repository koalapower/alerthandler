#!/bin/bash

mkdir /opt/alerthandler/
mkdir /opt/alerthandler/db/
mkdir /opt/alerthandler/certs/
mkdir /opt/alertmanager/

tar -xvf $1 --one-top-level=/opt/alerthandler/
tar -xvf $2 --one-top-level=/opt/alertmanager/ --strip-components=1

useradd -Mrs /usr/bin/false alerthandler
useradd -Mrs /usr/bin/false alertmanager


PYTHON="$(which python3)"
sed -i "s|python3|$PYTHON|g" /opt/alerthandler/templates/alerthandler/alerthandler.service

cp /opt/alerthandler/templates/alerthandler/alerthandler.service /etc/systemd/system/
cp /opt/alerthandler/templates/alerthandler/config.yml /opt/alerthandler/

cp /opt/alerthandler/templates/alertmanager/alertmanager.yml /opt/alertmanager/
cp /opt/alerthandler/templates/alertmanager/email.tmpl /opt/alertmanager/
cp /opt/alerthandler/templates/alertmanager/alertmanager.service /etc/systemd/system/

chown -R alertmanager:alertmanager /opt/alertmanager
chown -R alerthandler:alerthandler /opt/alerthandler
