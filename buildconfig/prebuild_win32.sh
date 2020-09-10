#!/bin/bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wget wine wine64 xvfb
