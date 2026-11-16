#!/bin/sh
# Sätter nytt versionsnummer i index.html och version.json före varje uppladdning
B=$(date +%Y%m%d-%H%M)
sed -i "s/^const BUILD = '[^']*';/const BUILD = '$B';/" index.html
printf '{ "build": "%s" }\n' "$B" > version.json
echo "$B"
