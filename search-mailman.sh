#!/bin/bash
ssh mailman 'find /var/lib/mailman/lists -mindepth 1 -maxdepth 1 -not -empty -type d' | sed -e 's/.*\///' -e '/\./!d'
