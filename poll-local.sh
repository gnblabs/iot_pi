#!/bin/bash

while true; do
  # Make GET request using curl
  curl --connection-timeout 15 -X GET http://192.168.1.104:3000/bedMap

  # Sleep for 1 second before making the next request
  sleep 4
done
