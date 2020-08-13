#!/bin/bash

set -e

psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /usr/src/db_template.sql
