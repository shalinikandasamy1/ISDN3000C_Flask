#!/bin/bash

RDK_USER=sunrise
RDK_IP=192.168.127.10
RDK_DIR=/home/sunrise/ISDN3000C_Final_Project
LOCAL_DIR=/Users/shalini/Downloads/ISDN3000C_Flask

while true; do
  rsync -av --delete $RDK_USER@$RDK_IP:$RDK_DIR/photos/         $LOCAL_DIR/photos/
  rsync -av --delete $RDK_USER@$RDK_IP:$RDK_DIR/photos_bw/      $LOCAL_DIR/photos_bw/
  rsync -av --delete $RDK_USER@$RDK_IP:$RDK_DIR/photos_vintage/ $LOCAL_DIR/photos_vintage/
  sleep 10
done
