#!/bin/bash

# Check if data directory exists
if [ ! -d "data" ]; then
  mkdir "data"
  echo "Created 'data' directory for downloaded files."
fi

# Get the filename argument
filename="$1"

# Check if filename is provided
if [ -z "$filename" ]; then
  echo "Error: Please provide a filename as the argument."
  exit 1
fi

# Loop through each line in the text file
while IFS= read -r IDENTIFIER; do
  # Construct the URL with the identifier
  URL="https://chaplaincyandspiritualcare.com/$IDENTIFIER"
  download_attempts=0

  # Download loop with retries
  while [ $download_attempts -lt 3 ]; do
    # Download the HTML with wget
    wget -q -O "cpe_data/$IDENTIFIER.html" "$URL"

    # Check download status
    if [ $? -eq 0 ]; then
      echo "Downloaded: $URL"
      sleep 1  # Sleep for 1 second on success
      break;  # Exit the download loop on success
    else
      echo "Error downloading: $URL (Attempt: $((download_attempts + 1)))"
      sleep 5  # Sleep for 5 seconds on error
      download_attempts=$((download_attempts + 1))
    fi
  done

  # Handle retries exceeding limit
  if [ $download_attempts -eq 3 ]; then
    echo "Failed to download after 3 retries: $URL"
  fi
done < "$filename"  # Use the provided filename

echo "Download process complete."