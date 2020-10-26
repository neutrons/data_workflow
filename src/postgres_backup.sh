# Create backup
ID=`date +%Y%m%d`
test -d basebackup_${ID} || mkdir -m 0755 -p basebackup_${ID}
pg_basebackup -D basebackup_${ID} -z -F t

# Cleanup of WALs
BACKUP_MARKER=`ls -t archivedir|head -n1`
pg_archivecleanup -d archivedir ${BACKUP_MARKER}
