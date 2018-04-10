from subprocess import Popen, PIPE
import getpass
import MySQLdb
import sys
import subprocess
import requests
import socket
from urlparse import urlparse
import os

user = raw_input("Username: ")
passwd = getpass.getpass("Password: ")
all = len(sys.argv) > 1 and sys.argv[1] == "--all"


def execute_sh(sh):
    return subprocess.check_output("./" + sh).strip().split("\n")


def execute(cursor, file):
    _sql = None
    with open(file, 'r') as myfile:
        _sql = myfile.read()
    cursor.execute(_sql)
    return cursor.fetchall()


def getIP(d):
    try:
        ip = socket.gethostbyname(d)
        return ip
    except Exception:
        return "KO!!"


def getDestination(d):
    url = requests.get("http://" + d, verify=False).url
    parse = urlparse(url)
    return parse.netloc.split(":")[0]


def get_split(arr, size):
    l = list(zip(*[iter(arr)] * size))
    r = len(arr) % size
    l.append(arr[-r:])
    return l


def get_certbot(sts):
    return "certbot --apache --force-renewal -d " + " -d ".join(sts) + "\n"

db = MySQLdb.connect("mysql", user, passwd)

cursor = db.cursor()

sql = "select distinct site from ("

results = execute(cursor, 'search-wp.sql')

for row in results:
    sql = sql + "\n\t("
    sql = sql + "select domain site from " + row[0] + "." + row[1]
    if not all:
        sql = sql + " where deleted=0"
    sql = sql + ") "
    sql = sql + "\n\tUNION"

sql = sql[:-7]

sql = sql + "\n) T order by site"

try:
    cursor.execute(sql)
except Exception as e:
    print sql
    raise e

sites = []

results = cursor.fetchall()
for row in results:
    sites.append(row[0])

db.close()

for site in execute_sh("search-apache.sh") + execute_sh("search-mailman.sh"):
    if site not in sites:
        sites.append(site)

sites = sorted(sites)

if os.path.isfile("blacklist.txt"):
    with open("blacklist.txt", "r") as f:
        blacklist = [l.strip() for l in f.readlines() if len(l.strip()) > 0]
        if len(blacklist) > 0:
            sites = list(set(sites) - set(blacklist))
sites = sorted(sites)

if not all:
    ip = requests.get('http://ip.42.pl/raw').text
    for i in range(len(sites) - 1, -1, -1):
        s = sites[i]
        s_ip = getIP(s)
        if ip != s_ip:
            print ip + " != %14s = %s" % (s_ip, s)
            del sites[i]
        '''
        else:
            d=getDestination(site)
            if d != site:
                print "%s ----> %s" (site, d)
                del sites[i]
	'''
    print ""

MAX_DOM = 100
domains = sorted(list(set(map(lambda x: ".".join(x.split(".")[-2:]), sites))))

f1 = open("certbot.sh", "w")
f1.write("#!/bin/bash\n")

f2 = open("check-ssl.sh", "w")
f2.write('''#!/bin/bash
check () {
  echo -n "$1 "
  if true | openssl s_client -connect $1:443 2>/dev/null | openssl x509 -noout -checkend 0 >/dev/null; then
    echo "OK"
  else
    echo "KO"
  fi
}
''')

for d in domains:
    print d
    sts = [d] + [s for s in sites if s.endswith("." + d)]
    print "\t" + '\n\t'.join(sts)
    for s in sts:
        f2.write("check "+s+"\n")
    if len(sts) <= MAX_DOM:
        f1.write("\n# " + d + "\n\n")
        f1.write(get_certbot(sts))
    else:
        count = 1
        for stsX in get_split(sts, MAX_DOM):
            f1.write("\n# " + d + " PART " + str(count)
                    + " - " + str(len(stsX)) + " items\n\n")
            f1.write(get_certbot(stsX))
            count = count + 1

f1.close()
f2.close()
