#!/bin/sh
mkdir /home/travis/.config/earthengine
echo '{"refresh_token": "'$EE_KEY'"}' > /home/travis/.config/earthengine/credentials

# End
