#!/usr/bin/env python3
"""
Script per aggiornare database con campi mancanti
"""

from app import app, db

def fix_database_fields():
    """Aggiunge campi mancanti alle tabelle esistenti"""

    with app.app_context():
        try:
            print("Controllo campi database...")

            with db.engine.connect() as connection:
                # Controlla campo numero_offerta_fornitore
                result = connection.execute(
                    db.text("SELECT COUNT(*) FROM pragma_table_info('ordine_fornitore') WHERE name='numero_offerta_fornitore'")
                ).fetchone()

                if result[0] == 0:
                    connection.execute(
                        db.text("ALTER TABLE ordine_fornitore ADD COLUMN numero_offerta_fornitore VARCHAR(100)")
                    )
                    print("OK Campo 'numero_offerta_fornitore' aggiunto")
                else:
                    print("OK Campo 'numero_offerta_fornitore' gia presente")

                # Controlla campo data_offerta_fornitore
                result = connection.execute(
                    db.text("SELECT COUNT(*) FROM pragma_table_info('ordine_fornitore') WHERE name='data_offerta_fornitore'")
                ).fetchone()

                if result[0] == 0:
                    connection.execute(
                        db.text("ALTER TABLE ordine_fornitore ADD COLUMN data_offerta_fornitore DATE")
                    )
                    print("OK Campo 'data_offerta_fornitore' aggiunto")
                else:
                    print("OK Campo 'data_offerta_fornitore' gia presente")

                connection.commit()
                print("✅ Database aggiornato con successo!")

        except Exception as e:
            print(f"ERRORE durante aggiornamento database: {e}")
            return False

        return True

if __name__ == "__main__":
    success = fix_database_fields()
    if success:
        print("Database pronto per l'uso!")
    else:
        print("Problemi nell'aggiornamento database")