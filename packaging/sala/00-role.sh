#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 --set app_password="$(cat /run/secrets/db_password)" <<'SQL'
CREATE ROLE faccupoint LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE faccupoint TO faccupoint;
GRANT USAGE, CREATE ON SCHEMA public TO faccupoint;
SQL
