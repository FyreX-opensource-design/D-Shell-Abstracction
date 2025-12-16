#!/usr/bin/env bash

if ! pgrep gtklock &> /dev/null; then
    gtklock
fi