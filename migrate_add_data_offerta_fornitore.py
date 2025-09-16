#!/usr/bin/env python3
"""
Migrazione Database: Aggiunge campo data_offerta_fornitore
"""

from app import app, db

def add_data_offerta_fornitore_field():
    """Aggiunge il campo data_offerta_fornitore alla tabella ordine_fornitore"""

    with app.app_context():
        try:
            # Verifica se il campo esiste già
            with db.engine.connect() as connection:
                result = connection.execute(
                    db.text("SELECT COUNT(*) FROM pragma_table_info('ordine_fornitore') WHERE name='data_offerta_fornitore'")
                ).fetchone()

                if result[0] == 0:
                    # Aggiungi il campo
                    connection.execute(
                        db.text("ALTER TABLE ordine_fornitore ADD COLUMN data_offerta_fornitore DATE")
                    )
                    connection.commit()
                    print("OK Campo 'data_offerta_fornitore' aggiunto con successo!")
                else:
                    print("INFO Campo 'data_offerta_fornitore' gia presente")

        except Exception as e:
            print(f"ERRORE durante aggiunta campo: {e}")

if __name__ == "__main__":
    add_data_offerta_fornitore_field()