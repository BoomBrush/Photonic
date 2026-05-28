#!/bin/bash

echo START ACTION
echo $ACTION
echo $ARGUMENT
echo END ACTION

if [ $ACTION = "download" ]; then
   sleep 1
   python client.py $ARGUMENT
fi
