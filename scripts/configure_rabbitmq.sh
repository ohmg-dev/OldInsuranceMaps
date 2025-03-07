#! /bin/bash

# this script assumes you have username/password in .env,
# and that rabbitmq-server has been installed.

echo "make sure you have RABBITMQ_USER and RABBITMQ_PASSWORD set in .env"\
	"and that these are the same values as are used in BROKER_URL."

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

sudo rabbitmqctl stop_app
sudo rabbitmqctl reset
sudo rabbitmqctl start_app

sudo rabbitmqctl delete_user guest
sudo rabbitmqctl add_user $RABBITMQ_USER $RABBITMQ_PASSWORD
sudo rabbitmqctl set_user_tags $RABBITMQ_USER administrator
sudo rabbitmqctl add_vhost /localhost
sudo rabbitmqctl set_permissions -p / $RABBITMQ_USER ".*" ".*" ".*"
sudo rabbitmqctl set_permissions -p /localhost $RABBITMQ_USER ".*" ".*" ".*"
