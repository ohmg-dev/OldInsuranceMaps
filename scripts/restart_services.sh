#! /usr/bin/bash

echo "restart celery_main"
sudo systemctl restart celery_main
echo "restart celery_mosaic"
sudo systemctl restart celery_main
echo "restart uwsgi"
sudo systemctl restart celery_main
