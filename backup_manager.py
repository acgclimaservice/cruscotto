import os
import shutil
import sqlite3
from datetime import datetime

def backup_database():
    """Backup rapido del database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('backups', exist_ok=True)
    
    # Backup database
    shutil.copy2('ddt_database.db', f'backups/db_backup_{timestamp}.db')
    print(f"✓ Backup creato: db_backup_{timestamp}.db")
    
    # Mantieni solo ultimi 5 backup
    backups = sorted([f for f in os.listdir('backups') if f.endswith('.db')])
    for old_backup in backups[:-5]:
        os.remove(f'backups/{old_backup}')
        print(f"✗ Rimosso vecchio: {old_backup}")

if __name__ == "__main__":
    backup_database()
