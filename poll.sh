#!/bin/bash

while true; do
  # Make GET request using curl
  curl -X GET http://localhost:3000/bedMap

  # Sleep for 1 second before making the next request
  sleep 5
done
