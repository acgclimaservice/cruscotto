#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

# Backup giornaliero
backup_dir = '/home/$USER/backups'
os.makedirs(backup_dir, exist_ok=True)

# Backup database
timestamp = datetime.now().strftime('%Y%m%d')
shutil.copy2('/home/$USER/mysite/ddt_database.db', 
             f'{backup_dir}/ddt_backup_{timestamp}.db')

# Mantieni solo ultimi 7 backup
backups = sorted(os.listdir(backup_dir))
for old in backups[:-7]:
    os.remove(f'{backup_dir}/{old}')

print(f"Backup completato: {timestamp}")
