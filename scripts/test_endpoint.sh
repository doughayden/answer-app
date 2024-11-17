#!/bin/bash

# Determine the directory of the script.
if [ -n "$BASH_SOURCE" ]; then
  # Bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "$ZSH_VERSION" ]; then
  # Zsh
  SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
else
  # Fallback for other shells
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

# Get the custom audience, and get an impersonated ID token.
source "$SCRIPT_DIR/set_audience_and_token.sh"

# Test the API endpoint.
echo "CURL RESULTS:"
echo ""
curl -X GET -H "Authorization: Bearer ${TOKEN}" "${AUDIENCE}/healthz"
echo ""
echo ""
