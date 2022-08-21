OUTPUT=$(echo "`date +"%Y-%m-%d-%H-%M"`")
echo ["`date +"%b %d %H:%M"`"] Beginning backup
pg_dump -h 178.28.0.14 -p 5432 -U postgres -d mewbot -w -Fc > "/home/ubuntu/backups/postgres-backups/${OUTPUT}.dump"
mongodump --uri mongodb://localhost:27017 -o "/home/ubuntu/backups/mongo-backups/${OUTPUT}"
echo ["`date +"%b %d %H:%M"`"] Finished backup
