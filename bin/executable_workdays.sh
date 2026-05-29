#!/usr/bin/env python3

import datetime
import calendar
import sys

def get_workdays(mode="month"):
    today = datetime.date.today()
    
    if mode == "today":
        # Calculate remaining days in month
        _, last_day = calendar.monthrange(today.year, today.month)
        start_date = today + datetime.timedelta(days=1)
        end_date = datetime.date(today.year, today.month, last_day)
    else:
        # Full month (skipping past days in month logic? Original script did:
        # dates starting from 1st of month.
        start_date = datetime.date(today.year, today.month, 1)
        _, last_day = calendar.monthrange(today.year, today.month)
        end_date = datetime.date(today.year, today.month, last_day)

    current = start_date
    while current <= end_date:
        # Monday=0, Sunday=6
        if current.weekday() < 5: # Mon-Fri
            print(current.strftime("%d.%m.%Y"))
        current += datetime.timedelta(days=1)

def main():
    mode = "month"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    get_workdays(mode)

if __name__ == "__main__":
    main()