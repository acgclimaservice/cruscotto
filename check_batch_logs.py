#!/usr/bin/env python3
"""
Script per controllare i batch job e i log di processing
"""

from app import app, db
from models import BatchImportJob, BatchImportFile, DDTIn

def check_batch_status():
    with app.app_context():
        print("=== VERIFICA BATCH JOBS ===")

        # Trova gli ultimi batch job
        jobs = BatchImportJob.query.order_by(BatchImportJob.created_at.desc()).limit(5).all()

        for job in jobs:
            print(f"\nJob ID: {job.id}")
            print(f"Status: {job.status}")
            print(f"Created: {job.created_at}")
            print(f"Metadata: {job.metadata}")
            print(f"Total files: {job.total_files}")
            print(f"Processed: {job.processed_files}")
            print(f"Successful: {job.successful_files}")
            print(f"Failed: {job.failed_files}")

            # Controlla i file del batch
            batch_files = BatchImportFile.query.filter_by(job_id=job.id).all()
            print(f"File nel batch: {len(batch_files)}")

            for bf in batch_files:
                print(f"  - {bf.original_filename}: {bf.status}")
                if bf.error_message:
                    print(f"    Errore: {bf.error_message}")
                if bf.ddt_in_id:
                    print(f"    DDT creato: {bf.ddt_in_id}")

        print("\n=== ULTIMI DDT IN ===")
        ddts = DDTIn.query.order_by(DDTIn.id.desc()).limit(5).all()
        for ddt in ddts:
            print(f"DDT {ddt.id}: {ddt.fornitore} - {ddt.riferimento} - {ddt.stato}")

if __name__ == '__main__':
    check_batch_status()