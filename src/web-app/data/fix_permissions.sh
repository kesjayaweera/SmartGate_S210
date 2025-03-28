#!/usr/bin/bash

# Change ownership to the user (user ID: tal, group ID: tal)
chown -R $USER:$USER ./postgresql

# Change permissions to allow reading and executing files
chmod -R 755 ./postgresql

# Print a message indicating success
echo "Permissions and ownership for ./postgresql have been fixed."

