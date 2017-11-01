#!/bin/bash
echo "Run with sudo"
gcc -o drop drop.c
sudo chown root:root ./drop
sudo chmod u+s ./drop
./drop
