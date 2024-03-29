#!/bin/python
from markdownTable import markdownTable
from transmission_rpc import Client

movies = Client(
    username="ervin",
    password="4663",
    host="ervinpopescu.ddns.net",
    port=9091,
)
shows = Client(
    username="ervin",
    password="4663",
    host="ervinpopescu.ddns.net",
    port=9092,
)

l = list({})

movies_session = movies.get_session()
movies_torrents = movies.get_torrents()
movies_torrents.sort(key=lambda f: f.name)

shows_session = shows.get_session()
shows_torrents = shows.get_torrents()
shows_torrents.sort(key=lambda f: f.name)

for movie in movies_torrents:
    eta = movie.format_eta()
    if eta == "not available":
        eta = "n/a"
    if eta == "unknown":
        eta = "unk"
    status = movie.status
    if status == "downloading":
        status = "down"
    if status == "seeding":
        status = "up"
    l.append(
        {
            "NAME": f" {movie.name[:26]} ",
            "STAT": status,
            "PROG": f" {str(movie.progress)} ",
            "DOWN": f" {str(movie.rateDownload / 1000000.0)} ",
            "ETA": f" {eta} ",
        }
    )
table = (
    markdownTable(l)
    .setParams(
        row_sep="markdown",
        quote=False,
        padding_weight="center",
        # multiline=True,
    )
    .getMarkdown()
)
print(table)
print("")
print("")
l = []
for show in shows_torrents:
    eta = show.format_eta()
    if eta == "not available":
        eta = "n/a"
    if eta == "unknown":
        eta = "unk"
    status = show.status
    if status == "downloading":
        status = "down"
    if status == "seeding":
        status = "up"
    l.append(
        {
            "NAME": f" {show.name[:26]} ",
            "STAT": status,
            "PROG": f" {str(show.progress)} ",
            "DOWN": f" {str(show.rateDownload / 1000000.0)} ",
            "ETA": f" {eta} ",
        }
    )

table = (
    markdownTable(l)
    .setParams(
        row_sep="markdown",
        quote=False,
        padding_weight="center",
        # multiline=True,
    )
    .getMarkdown()
)
print(table)
# outfile = open("/home/ervin/torrent_status.md", "w")
# outfile.write(table)
# outfile.write("\n")
# outfile.close()
