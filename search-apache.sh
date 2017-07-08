#!/bin/bash
grep ServerName -rh /etc/apache2/sites-available/ | sed -e '/^\s*#/d' -e 's/\s*ServerName\s*//' -e '/^\$/d' -e 's/\*\.*//' | sort | uniq

