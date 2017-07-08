from subprocess import Popen, PIPE
import getpass
import MySQLdb
import sys
import subprocess

user = raw_input("Username: ")
passwd = getpass.getpass("Password: ")
all = len(sys.argv)>1 and sys.argv[1] == "--all"

def execute_sh(sh):
	return subprocess.check_output("./"+sh).split("\n")

def execute(cursor,file):
	_sql=None
	with open(file, 'r') as myfile:
		_sql=myfile.read()
	cursor.execute(_sql)
	return cursor.fetchall()


db = MySQLdb.connect("mysql", user, passwd)

cursor = db.cursor()

sql="select distinct site from ("

results = execute(cursor, 'search-wp.sql')

for row in results:
	sql = sql+"\n\t("
	sql = sql+"select domain site from "+row[0]+"."+row[1]
	sql = sql+") "
	sql = sql+"\n\tUNION"

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

for site in execute_sh("search-apache.sh"):
	if len(site)>0 and site not in sites:
		sites.append(site)

domains=sorted(list(set(map(lambda x: ".".join(x.split(".")[-2:]), sites))))

with open("certbot.sh","w") as f:
	f.write("#!/bin/bash\n")
	for d in domains:
		print d
		sts=[d]
		for site in sites:
			if d!=site and site.endswith(d):
				print "\t"+site
				sts.append(site)
		f.write("\n# "+d+"\n\n")
		f.write("certbot --apache -d " + " -d ".join(sts)+"\n")
