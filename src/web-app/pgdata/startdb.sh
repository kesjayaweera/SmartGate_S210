#!/usr/bin/bash

[ -d /run/postgresql ] || mkdir /run/postgresql
[ -O /run/postgresql ] || chown $USER:$USER /run/postgresql
chmod 775 /run/postgresql
pg_ctl -D . start

