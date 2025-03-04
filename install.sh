#!/bin/bash


echo "***Creating directories***"

mkdir /opt/alerthandler/
mkdir /opt/alerthandler/db/
mkdir /opt/alerthandler/certs/
mkdir /opt/alertmanager/

echo "***Unarchive alertmanager***"

tar -xvf alertmanager-0.28.0.linux-amd64.tar.gz --one-top-level=/opt/alertmanager/ --strip-components=1

echo "***Installing python packages***"

python3 -m pip install -r requirements.txt

echo "***Copying neccessary files***"

cp src/* /opt/alerthandler/
PYTHON="$(which python3)"
sed -i "s|python3|$PYTHON|g" templates/alerthandler/alerthandler.service
cp templates/alerthandler/config.yml /opt/alerthandler/
cp templates/alerthandler/alerthandler.service /etc/systemd/system/

cp templates/alertmanager/alertmanager.yml /opt/alertmanager/
cp templates/alertmanager/email.tmpl /opt/alertmanager/
cp templates/alertmanager/alertmanager.service /etc/systemd/system/

echo "***Creating users***"

useradd -Mrs /usr/bin/false alerthandler
useradd -Mrs /usr/bin/false alertmanager

echo "***Chowning directories***"

chown -R alertmanager:alertmanager /opt/alertmanager
chown -R alerthandler:alerthandler /opt/alerthandler

echo "***Installation complete***"
