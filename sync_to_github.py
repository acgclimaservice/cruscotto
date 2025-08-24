#!/usr/bin/env python3
"""
SYNC LOCALE → GITHUB per Cruscotto DDT
Salva questo file nella root del tuo progetto
"""

import subprocess
import os
import sys
from datetime import datetime

# Colori per output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def run_command(cmd, capture=False):
    """Esegue un comando e mostra l'output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            return subprocess.run(cmd, shell=True).returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def sync_to_github():
    """Sincronizza modifiche locali con GitHub"""
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 SYNC LOCALE → GITHUB{Colors.RESET}")
    print("=" * 50)
    
    # 1. Verifica se siamo in un repository git
    if not os.path.exists('.git'):
        print(f"{Colors.RED}❌ Errore: Non sei in un repository Git!{Colors.RESET}")
        print(f"\nInizializza con:")
        print(f"  git init")
        print(f"  git remote add origin https://github.com/acgclimaservice/cruscotto.git")
        return False
    
    # 2. Controlla lo stato
    print(f"\n{Colors.YELLOW}📊 Controllo stato...{Colors.RESET}")
    success, status, _ = run_command("git status --short", capture=True)
    
    if not status.strip():
        print(f"{Colors.GREEN}✅ Nessuna modifica da sincronizzare{Colors.RESET}")
        return True
    
    print(f"Modifiche trovate:")
    print(status)
    
    # 3. Mostra i file modificati
    modified_files = status.strip().split('\n')
    print(f"\n{Colors.YELLOW}📝 File modificati: {len(modified_files)}{Colors.RESET}")
    
    # 4. Chiedi conferma
    risposta = input(f"\n{Colors.BOLD}Vuoi procedere con il commit? (s/n): {Colors.RESET}").lower()
    if risposta != 's':
        print(f"{Colors.YELLOW}❌ Operazione annullata{Colors.RESET}")
        return False
    
    # 5. Git add
    print(f"\n{Colors.YELLOW}📦 Aggiunta file...{Colors.RESET}")
    success, _, _ = run_command("git add .")
    if success:
        print(f"{Colors.GREEN}✅ File aggiunti{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Errore nell'aggiunta file{Colors.RESET}")
        return False
    
    # 6. Messaggio commit
    print(f"\n{Colors.YELLOW}💬 Messaggio commit{Colors.RESET}")
    default_msg = f"Update {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    custom_msg = input(f"Messaggio (invio per '{default_msg}'): ").strip()
    commit_msg = custom_msg if custom_msg else default_msg
    
    # 7. Git commit
    print(f"\n{Colors.YELLOW}💾 Creazione commit...{Colors.RESET}")
    success, _, error = run_command(f'git commit -m "{commit_msg}"', capture=True)
    if success:
        print(f"{Colors.GREEN}✅ Commit creato: {commit_msg}{Colors.RESET}")
    else:
        if "nothing to commit" in error:
            print(f"{Colors.YELLOW}ℹ️ Niente da committare{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Errore commit: {error}{Colors.RESET}")
            return False
    
    # 8. Git push
    print(f"\n{Colors.YELLOW}📤 Upload su GitHub...{Colors.RESET}")
    print("(potrebbe richiedere username/password)")
    
    success, _, error = run_command("git push origin main", capture=True)
    if not success:
        # Prova con master se main non esiste
        success, _, _ = run_command("git push origin master", capture=True)
    
    if success:
        print(f"\n{Colors.GREEN}{'='*50}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SINCRONIZZAZIONE COMPLETATA!{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*50}{Colors.RESET}")
        print(f"\n{Colors.BLUE}📌 Prossimi passi:{Colors.RESET}")
        print(f"1. Vai su PythonAnywhere")
        print(f"2. Esegui: {Colors.BOLD}~/sync.sh{Colors.RESET}")
        print(f"\n{Colors.BLUE}🔗 Repository: https://github.com/acgclimaservice/cruscotto{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Errore push: {error}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Possibili soluzioni:{Colors.RESET}")
        print(f"1. Verifica le credenziali GitHub")
        print(f"2. Controlla la connessione internet")
        print(f"3. Verifica che il branch sia 'main' o 'master'")
        return False
    
    return True

def quick_sync():
    """Sync veloce con commit automatico"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}⚡ QUICK SYNC{Colors.RESET}")
    
    if not os.path.exists('.git'):
        print(f"{Colors.RED}❌ Non in un repository Git!{Colors.RESET}")
        return False
    
    # Auto commit e push
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    commands = [
        ("git add .", "Aggiunta file"),
        (f'git commit -m "Quick update {timestamp}"', "Commit"),
        ("git push origin main || git push origin master", "Push")
    ]
    
    for cmd, desc in commands:
        print(f"{Colors.YELLOW}→ {desc}...{Colors.RESET}")
        success, _, _ = run_command(cmd, capture=True)
        if success:
            print(f"{Colors.GREEN}  ✓ {desc} completato{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✅ Quick sync completato!{Colors.RESET}")
    print(f"Esegui {Colors.BOLD}~/sync.sh{Colors.RESET} su PythonAnywhere")

if __name__ == "__main__":
    # Check argomenti
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_sync()
    else:
        sync_to_github()