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

l = list(dict())

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
            "NAME": " " + movie.name[0:26] + " ",
            "STAT": status,
            "PROG": " " + str(movie.progress) + " ",
            "DOWN": " " + str(movie.rateDownload / 1e6) + " ",
            "ETA": " " + eta + " ",
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
            "NAME": " " + show.name[0:26] + " ",
            "STAT": status,
            "PROG": " " + str(show.progress) + " ",
            "DOWN": " " + str(show.rateDownload / 1e6) + " ",
            "ETA": " " + eta + " ",
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
