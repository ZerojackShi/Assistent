#!/bin/bash

# Find the path of libpython3.9.so
python_lib_path=$(find /usr/lib64 /usr/lib -name libpython3.9.so* 2>/dev/null)

if [ -n "$python_lib_path" ]; then
    # Add the path to LD_LIBRARY_PATH
    export LD_LIBRARY_PATH="$python_lib_path:$LD_LIBRARY_PATH"
    echo "LD_LIBRARY_PATH updated with: $python_lib_path"
else
    echo "Error: libpython3.9.so not found."
fi

