#!/bin/bash

# start=$(date +%s%N)
# export PS4='+[$(((`date +%s%N`-$start)/1000000))ms][${BASH_SOURCE}:${LINENO}]: ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
# set -x

nr_days_in_month=$(cal | awk 'FNR>2{d+=NF}END{print d}')
current_day=$(date +%d)
remaining=$(awk -v n="$nr_days_in_month" -v c="$current_day" 'BEGIN {print n-c}')

case "$1" in
  "today")

    dates=$({ for d in $(seq 1 "$remaining")
      do
        date +%Y-%m-%d -d "$(date +%Y-%m-%d) +$d days"
      done
    } | sort)

    for d in $dates
    do
      case $(date -d "$d" "+%a") in
        Mon|Tue|Wed|Thu|Fri)
          printf "%s\n" "$(date +%d.%m.%Y -d "$d")";;
        *)
          continue;;
      esac
    done;;
  "")
    dates=$({ for d in $(seq 1 "$nr_days_in_month")
        do
          date +%Y-%m-%d -d "$(date +%Y-%m-01) +$d days"
        done
      } | sort)

      printf '%s\n' "$dates"

      for d in $dates
      do
        case $(date -d "$d" "+%a") in
          Mon|Tue|Wed|Thu|Fri)
            printf "%s\n" "$(date +%d.%m.%Y -d "$d")";;
          *)
            continue;;
        esac
      done;;
esac
