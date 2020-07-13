#!/bin/bash

pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /backup/gifsync-backup.sql

