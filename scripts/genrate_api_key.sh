#!/bin/bash

generate_token() {
  local length=22

  local charset=""
  charset+='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  charset+='abcdefghijklmnopqrstuvwxyz'
  charset+='0123456789'

  local token=""
  while [ ${#token} -lt "$length" ]; do
      # Generate a random number between 0 and the length of the charset
      local random_index=$(( ($RANDOM % 32768) % ${#charset} ))
      token+=${charset:$random_index:1}
  done

  echo $token > .ohmg_api_key
}

generate_token

echo "New API key saved. You must restart the webserver for the key to take effect."
