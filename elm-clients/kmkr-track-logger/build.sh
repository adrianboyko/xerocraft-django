#!/usr/bin/env bash
# Expects to be run in $ProjectFileDir$/elm-clients/kmkr-track-logger/

clear

set -x

ELM=src/KmkrTrackLogger.elm
JS=out/KmkrTrackLogger.js
MIN=../../kmkr/static/kmkr/KmkrTrackLogger.min.js

if elm-make --yes ${ELM} --output=${JS} && cat ${JS} > ${MIN}
#if elm-make --debug --yes ${ELM} --output=${JS} && minify ${JS} > ${MIN}
then
    sed -i "1i// Generated by Elm" ${JS}
    sed -i "1i// Generated by Elm" ${MIN}
fi

paplay /usr/share/sounds/ubuntu/stereo/dialog-information.ogg
