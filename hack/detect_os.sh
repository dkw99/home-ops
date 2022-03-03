#!/usr/bin/env bash

if [ "$(uname)" == "Darwin" ]; then
    D_OS="Darwin"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    D_OS="Linux"
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
    D_OS="MINGW32_NT"
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    D_OS="MINGW64_NT"
fi

export MACHINE_OS=$D_OS
