#!/bin/python

import time
import os

import requests
from markdownTable import markdownTable

data = requests.get("https://disease.sh/v3/covid-19/countries/RO").json()
date = time.strftime("%Y-%m-%d %H:%M", time.localtime())

needed = [
    "updated",
    "cases",
    "todayCases",
    "deaths",
    "todayDeaths",
    "recovered",
    "todayRecovered",
    "active",
    "critical",
    "casesPerOneMillion",
    "deathsPerOneMillion",
]

dir = os.listdir("/home/ervin/data/corona_tables")

if (
    "corona.md" not in dir
    or os.stat("/home/ervin/data/corona_tables/corona.md").st_size == 0
):
    list_of_data = [[]]
    for list in list_of_data:
        for i in needed:
            list.append(data[i])
    list_of_data[0][0] = time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(int(str(list_of_data[0][0])[:-3]))
    )
    list_of_data[0][:0] = [date]

    headers = [
        "Date",
        "Last updated",
        "Total",
        "Today",
        "Deaths",
        "Deaths Today",
        "Recovered",
        "Active",
        "Critical",
        "Deaths per million",
    ]
    d = [dict(zip(headers, list)) for list in list_of_data]
    table = markdownTable(d).setParams(row_sep="markdown", quote=False).getMarkdown()
    outfile = open("/home/ervin/data/corona_tables/corona.md", "w")
    outfile.write(table)
    outfile.write("\n")
    outfile.close()
else:
    l = []
    for i in needed:
        l.append(data[i])
    l[0] = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(str(l[0])[:-3])))
    l[:0] = [time.strftime("%Y-%m-%d %H:%M", time.localtime())]
    string = "|" + " | ".join(map(str, l))
    outfile = open("/home/ervin/data/corona_tables/corona.md", "a")
    outfile.write("\n")
    outfile.write(string)
    outfile.close()
