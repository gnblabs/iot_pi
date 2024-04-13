#!/bin/bash

while true; do
  # Make GET request using curl
  curl --max-time 15 http://localhost:3000

  # Sleep for 1 second before making the next request
  sleep 4
done
