#!/bin/bash

if command -v df >/dev/null; then
    # Use -h for human readable (powers of 1024) or -H for powers of 1000. 
    # The original script used 1048576 (1024*1024), so it meant MiB -> GiB.
    # df -h is generally preferred.
    
    # Calculate total used and total size across all mounted filesystems?
    # Original script summed up all lines.
    
    # Note: Summing up usage of all mounts might count binds/tmpfs double.
    # But sticking to original logic with cleaner implementation:
    
    df -k | awk 'NR>1 {used+=$3; total+=$2} END {printf "%.2fG / %.2fG", used/1048576, total/1048576}'
else
    echo "Error: df command not found"
    exit 1
fi
