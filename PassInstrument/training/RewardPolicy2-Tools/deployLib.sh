#!/bin/bash
cd sharedLib
# build .so
make clean && make
sudo mkdir -p /opt/lib
sudo cp libfunctime.so.1.0 /opt/lib
sudo ln -sf /opt/lib/libfunctime.so.1.0 /opt/lib/libfunctime.so.1
sudo ln -sf /opt/lib/libfunctime.so.1 /opt/lib/libfunctime.so
echo "Make sure the environment variables are proper set('C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LD_LIBRARY_PATH'and 'LIBRARY_PATH')."
