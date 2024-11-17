#!/bin/bash

# To call the deployed API: Set environment varialbes including the custom audience and token by sourcing the set_audience_and_token script.
# For local testing: expose the server on localhost and set the AUDIENCE variable manually.
# Example - 1st terminal:
# uvicorn api:app --reload --host 0.0.0.0 --port 8888
# Example - 2nd terminal:
# export AUDIENCE='localhost:8888'
# Then use the send_question script to send a question to the local server. (The token is not required for local testing and can be empty.)

# Check if the AUDIENCE variable is set. If not, set it by sourcing the set_audience_and_token script.
if [ -z ${AUDIENCE+x} ]; then
    echo "The AUDIENCE variable is not set. Set the AUDIENCE variable by sourcing the set_audience_and_token script."
    exit 1
fi

# Run the rest of this script until the caller interrupts it with Ctrl+C.
while true; do
    # Send a question to the Agent Builder Search app.
    echo "Enter a question to send to the Search app. Press Ctrl+C to exit..."
    echo ""
    echo ""
    echo "QUESTION: "
    echo ""
    read question
    echo ""
    echo "ANSWER:"
    echo ""
    curl -s -X POST -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d "{\"question\": \"$question\"}" "${AUDIENCE}/answer" | jq -r '.answer'
    echo ""
    echo ""
    # Ask the user to press any key to continue or Ctrl+C to exit.
    read -n 1 -s -r -p "Press any key to continue or Ctrl+C to exit..."
    # Clear the question variable.
    question=""
    # Clear the terminal output.
    clear
done
