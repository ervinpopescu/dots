#!/bin/bash

os=$(uname -s)

if [ "$os" = "Linux" ]; then
    # Linux logic using free
    if command -v free >/dev/null; then
        free -h | awk '/^Mem:/ {print $3 "/" $2}'
    else
        echo "N/A"
    fi
elif [ "$os" = "Darwin" ]; then
    # macOS logic
    vm_stat_out=$(vm_stat)
    
    # Get page size (in bytes)
    # Header: Mach Virtual Memory Statistics: (page size of 16384 bytes)
    page_size=$(echo "$vm_stat_out" | head -1 | grep -oE '[0-9]+')
    
    if [ -z "$page_size" ]; then
        page_size=4096 # Fallback
    fi

    # Extract pages (last field, remove trailing dot)
    # "Pages active: 639750." -> 639750
    # "Pages wired down: 128585." -> 128585
    pages_active=$(echo "$vm_stat_out" | awk '/Pages active/ {print $NF}' | tr -d '.')
    pages_wired=$(echo "$vm_stat_out" | awk '/Pages wired/ {print $NF}' | tr -d '.')
    pages_compressed=$(echo "$vm_stat_out" | awk '/Pages occupied by compressor/ {print $NF}' | tr -d '.')
    
    # Calculate used memory in Bytes -> MiB
    used_pages=$((pages_active + pages_wired + pages_compressed))
    used_mem_bytes=$((used_pages * page_size))
    used_mem_mib=$((used_mem_bytes / 1024 / 1024))
    
    # Total memory
    total_mem_bytes=$(sysctl -n hw.memsize)
    total_mem_gib=$((total_mem_bytes / 1024 / 1024 / 1024))
    
    echo "${used_mem_mib}Mi / ${total_mem_gib}Gi"
else
    echo "Unknown OS"
fi
