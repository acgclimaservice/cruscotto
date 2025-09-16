# document_templates.py
# Modelli per documenti DDT IN/OUT, Preventivi e Ordini
from datetime import datetime
from models import db
import base64
import os

class DocumentTemplate:
    """Classe base per template documenti"""
    
    # Dati aziendali ACG Clima Service S.R.L.
    COMPANY_DATA = {
        'ragione_sociale': 'ACG CLIMA SERVICE S.R.L.',
        'indirizzo': 'VIA DUCCIO GALIMBERTI, 47',
        'citta': 'ALESSANDRIA',
        'cap': '15121',
        'partita_iva': 'IT12345678901',  # Da verificare/aggiornare
        'codice_fiscale': 'ACG1234567890',  # Da verificare/aggiornare
        'telefono': '+39 0131 123456',  # Da verificare/aggiornare
        'email': 'info@acgclimaservice.com',
        'pec': 'acgclimaservice@pec.it',  # Da verificare/aggiornare
        'settore': 'Impianti termici e climatizzazione',
        'codice_ateco': '43.22.01',
        'descrizione_ateco': 'Installazione di impianti idraulici, di riscaldamento e di condizionamento dell\'aria'
    }
    
    @staticmethod
    def get_logo_base64():
        """Converte il logo in base64 per l'uso nei PDF"""
        try:
            logo_path = os.path.join('static', 'logo-acg.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = base64.b64encode(logo_file.read()).decode('utf-8')
                    return f"data:image/png;base64,{logo_data}"
        except Exception as e:
            print(f"Errore caricamento logo: {e}")
        return None
    
    @staticmethod
    def get_header_company():
        """Header comune con dati aziendali"""
        logo_base64 = DocumentTemplate.get_logo_base64()
        
        if logo_base64:
            logo_html = f'<img src="{logo_base64}" alt="ACG Clima Service" style="height: 60px; width: auto;">'
        else:
            logo_html = '<div class="logo-placeholder">ACG</div>'
            
        return f"""
        <div class="document-header">
            <div class="company-info">
                <h2>{DocumentTemplate.COMPANY_DATA['ragione_sociale']}</h2>
                <p>{DocumentTemplate.COMPANY_DATA['indirizzo']}<br>
                   {DocumentTemplate.COMPANY_DATA['cap']} {DocumentTemplate.COMPANY_DATA['citta']}</p>
                <p>P.IVA: {DocumentTemplate.COMPANY_DATA['partita_iva']} | 
                   C.F.: {DocumentTemplate.COMPANY_DATA['codice_fiscale']}</p>
                <p>Tel: {DocumentTemplate.COMPANY_DATA['telefono']} | 
                   Email: {DocumentTemplate.COMPANY_DATA['email']}</p>
                <p><strong>{DocumentTemplate.COMPANY_DATA['settore']}</strong></p>
            </div>
            <div class="document-logo">
                {logo_html}
            </div>
        </div>
        """

    @staticmethod
    def get_styles():
        """Stili CSS base per tutti i documenti"""
        return """
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        .document-header { display: flex; justify-content: space-between; border-bottom: 2px solid #003366; padding-bottom: 20px; margin-bottom: 20px; }
        .company-info h2 { color: #003366; margin: 0 0 10px 0; }
        .company-info p { margin: 2px 0; font-size: 14px; }
        .logo-placeholder { width: 80px; height: 80px; background: #003366; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; border-radius: 8px; }
        .document-title { text-align: center; margin: 30px 0; }
        .document-title h1 { color: #003366; margin-bottom: 10px; }
        .document-number { background: #f8f9fa; padding: 10px; border-radius: 5px; font-weight: bold; }
        .document-details { display: flex; gap: 30px; margin: 30px 0; }
        .section { flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .section h3 { color: #003366; margin-top: 0; }
        .articles-table { margin: 30px 0; }
        .articles-table h3 { color: #003366; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #ddd; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #003366; color: white; font-weight: bold; }
        .total-row { background: #f8f9fa; font-weight: bold; }
        .document-footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 20px; }
        """


class DDTInTemplate(DocumentTemplate):
    """Template per DDT IN (Documento di Trasporto in Entrata)"""
    
    @staticmethod
    def generate_html(ddt_data):
        """Genera HTML per DDT IN"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>DDT IN - {ddt_data.get('numero_ddt', 'N/A')}</title>
            <style>{DDTInTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>DOCUMENTO DI TRASPORTO IN ENTRATA</h1>
                <div class="document-number">DDT N. {ddt_data.get('numero_ddt', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>DATI FORNITORE</h3>
                    <p><strong>{ddt_data.get('fornitore', 'N/A')}</strong></p>
                    <p>Data DDT Origine: {ddt_data.get('data_ddt_origine', 'N/A')}</p>
                    <p>Numero DDT Origine: {ddt_data.get('numero_ddt_origine', 'N/A')}</p>
                    <p>Riferimento: {ddt_data.get('riferimento', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h3>DESTINAZIONE</h3>
                    <p>{ddt_data.get('destinazione', 'N/A')}</p>
                    <p>Data Ricevimento: {current_date}</p>
                    <p>Stato: {ddt_data.get('stato', 'N/A').upper()}</p>
                </div>
            </div>
            
            <div class="articles-table">
                <h3>ARTICOLI RICEVUTI</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Codice</th>
                            <th>Descrizione</th>
                            <th>Quantità</th>
                            <th>U.M.</th>
                            <th>Costo Unit.</th>
                            <th>Totale</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Aggiungi articoli (se presenti nei dati DDT)
        totale_generale = 0
        if hasattr(ddt_data, 'get') and 'articoli' in ddt_data:
            for articolo in ddt_data['articoli']:
                subtotal = float(articolo.get('quantita', 0)) * float(articolo.get('costo_unitario', 0))
                totale_generale += subtotal
                html += f"""
                        <tr>
                            <td>{articolo.get('codice', 'N/A')}</td>
                            <td>{articolo.get('descrizione', 'N/A')}</td>
                            <td>{articolo.get('quantita', 0)}</td>
                            <td>{articolo.get('unita_misura', 'PZ')}</td>
                            <td>€ {float(articolo.get('costo_unitario', 0)):.2f}</td>
                            <td>€ {subtotal:.2f}</td>
                        </tr>
                """
        
        html += f"""
                    </tbody>
                    <tfoot>
                        <tr class="total-row">
                            <td colspan="5"><strong>TOTALE DOCUMENTO:</strong></td>
                            <td><strong>€ {totale_generale:.2f}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
            
            <div class="document-footer">
                <p>Documento generato automaticamente il {current_date}</p>
                <p>Sistema Gestione DDT - {DocumentTemplate.COMPANY_DATA['ragione_sociale']}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return """
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        .document-header { display: flex; justify-content: space-between; border-bottom: 2px solid #003366; padding-bottom: 20px; margin-bottom: 20px; }
        .company-info h2 { color: #003366; margin: 0 0 10px 0; }
        .company-info p { margin: 2px 0; font-size: 14px; }
        .logo-placeholder { width: 80px; height: 80px; background: #003366; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; border-radius: 8px; }
        .document-title { text-align: center; margin: 30px 0; }
        .document-title h1 { color: #003366; margin-bottom: 10px; }
        .document-number { background: #f8f9fa; padding: 10px; border-radius: 5px; font-weight: bold; }
        .document-details { display: flex; gap: 30px; margin: 30px 0; }
        .section { flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .section h3 { color: #003366; margin-top: 0; }
        .articles-table { margin: 30px 0; }
        .articles-table h3 { color: #003366; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #ddd; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #003366; color: white; font-weight: bold; }
        .total-row { background: #f8f9fa; font-weight: bold; }
        .document-footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 20px; }
        """


class DDTOutTemplate(DocumentTemplate):
    """Template per DDT OUT (Documento di Trasporto in Uscita)"""
    
    @staticmethod
    def generate_html(ddt_data):
        """Genera HTML per DDT OUT"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>DDT OUT - {ddt_data.get('numero_ddt', 'N/A')}</title>
            <style>{DDTOutTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>DOCUMENTO DI TRASPORTO IN USCITA</h1>
                <div class="document-number">DDT N. {ddt_data.get('numero_ddt', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>CLIENTE/DESTINATARIO</h3>
                    <p><strong>{ddt_data.get('nome_origine', 'N/A')}</strong></p>
                    <p>Destinazione: {ddt_data.get('destinazione', 'N/A')}</p>
                    <p>Riferimento: {ddt_data.get('riferimento', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h3>SPEDIZIONE</h3>
                    <p>Data Spedizione: {ddt_data.get('data_ddt_origine', current_date)}</p>
                    <p>Magazzino Partenza: {ddt_data.get('magazzino_partenza', 'N/A')}</p>
                    <p>Stato: {ddt_data.get('stato', 'N/A').upper()}</p>
                </div>
            </div>
            
            <div class="articles-table">
                <h3>ARTICOLI SPEDITI</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Codice</th>
                            <th>Descrizione</th>
                            <th>Quantità</th>
                            <th>U.M.</th>
                            <th>Prezzo Unit.</th>
                            <th>Totale</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Aggiungi articoli (se presenti nei dati DDT)
        totale_generale = 0
        if 'articoli' in ddt_data and ddt_data['articoli']:
            for articolo in ddt_data['articoli']:
                subtotal = float(articolo.get('quantita', 0)) * float(articolo.get('prezzo_unitario', 0))
                totale_generale += subtotal
                html += f"""
                        <tr>
                            <td>{articolo.get('codice', 'N/A')}</td>
                            <td>{articolo.get('descrizione', 'N/A')}</td>
                            <td>{articolo.get('quantita', 0)}</td>
                            <td>{articolo.get('unita_misura', 'PZ')}</td>
                            <td>€ {float(articolo.get('prezzo_unitario', 0)):.2f}</td>
                            <td>€ {subtotal:.2f}</td>
                        </tr>
                """
        else:
            html += """
                        <tr>
                            <td colspan="6" style="text-align: center; padding: 30px; color: #666;">
                                Nessun articolo presente
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                    <tfoot>
                        <tr class="total-row">
                            <td colspan="5"><strong>TOTALE DOCUMENTO:</strong></td>
                            <td><strong>€ """ + f"{totale_generale:.2f}" + """</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
            
            <div class="transport-info">
                <h3>INFORMAZIONI TRASPORTO</h3>
                <div class="transport-grid">
                    <div>Trasporto a cura: MITTENTE</div>
                    <div>Causale trasporto: VENDITA</div>
                    <div>N. Colli: 1</div>
                    <div>Peso: DA DEFINIRE</div>
                </div>
            </div>
            
            <div class="document-footer">
                <div class="signatures">
                    <div>Firma Mittente<br><br>_________________</div>
                    <div>Firma Destinatario<br><br>_________________</div>
                </div>
                <p>Documento generato automaticamente il {current_date}</p>
                <p>Sistema Gestione DDT - {DocumentTemplate.COMPANY_DATA['ragione_sociale']}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return DocumentTemplate.get_styles() + """
        .transport-info { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .transport-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }
        .signatures { display: flex; justify-content: space-between; margin: 40px 0 20px 0; }
        .signatures div { text-align: center; }
        """


class MPLSTemplate(DocumentTemplate):
    """Template per MPLS (Margine, Prezzo, Lavoro, Servizio)"""
    
    @staticmethod
    def generate_html(mpls_data):
        """Genera HTML per MPLS con stile DDT OUT"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>MPLS - {mpls_data.get('numero_mpls', 'N/A')}</title>
            <style>{MPLSTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>PREVENTIVO MARGINI PREZZI LISTINO SCONTI</h1>
                <div class="document-number">MPLS N. {mpls_data.get('numero_mpls', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>CLIENTE</h3>
                    <p><strong>{mpls_data.get('cliente_nome', 'N/A')}</strong></p>
                    <p>Codice Cliente: {mpls_data.get('cliente_codice', 'N/A')}</p>
                    <p>Indirizzo: {mpls_data.get('indirizzo', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h3>DETTAGLI MPLS</h3>
                    <p>Data Creazione: {mpls_data.get('data_creazione', current_date)}</p>
                    <p>Stato: {mpls_data.get('stato', 'N/A').upper()}</p>
                    <p>Commessa: {mpls_data.get('commessa_numero', 'N/A')}</p>
                </div>
            </div>
            
            <div class="description-section">
                <h3>DESCRIZIONE LAVORI</h3>
                <p>{mpls_data.get('descrizione', 'N/A')}</p>
            </div>
            
            <div class="articles-table">
                <h3>ARTICOLI E CALCOLI</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Codice</th>
                            <th>Descrizione</th>
                            <th>Qty</th>
                            <th>Fornitore</th>
                            <th>Costo Unit.</th>
                            <th>Ricarico %</th>
                            <th>Prezzo Vendita</th>
                            <th>Totale</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Aggiungi articoli
        totale_costi = 0
        totale_vendita = 0
        
        if 'articoli' in mpls_data and mpls_data['articoli']:
            for articolo in mpls_data['articoli']:
                costo_totale = float(articolo.get('quantita', 0)) * float(articolo.get('prezzo_costo', 0))
                vendita_totale = float(articolo.get('quantita', 0)) * float(articolo.get('prezzo_vendita', 0))
                totale_costi += costo_totale
                totale_vendita += vendita_totale
                
                # Calcola ricarico
                ricarico = 0
                if articolo.get('prezzo_costo', 0) > 0 and articolo.get('prezzo_vendita', 0):
                    ricarico = ((float(articolo.get('prezzo_vendita', 0)) - float(articolo.get('prezzo_costo', 0))) / float(articolo.get('prezzo_costo', 0))) * 100
                
                html += f"""
                        <tr>
                            <td>{articolo.get('codice', 'N/A')}</td>
                            <td>{articolo.get('descrizione', 'N/A')}</td>
                            <td>{articolo.get('quantita', 0)}</td>
                            <td>{articolo.get('fornitore', 'N/A')}</td>
                            <td>€ {float(articolo.get('prezzo_costo', 0)):.2f}</td>
                            <td>{ricarico:.1f}%</td>
                            <td>€ {float(articolo.get('prezzo_vendita', 0)):.2f}</td>
                            <td>€ {vendita_totale:.2f}</td>
                        </tr>
                """
        else:
            html += """
                        <tr>
                            <td colspan="8" style="text-align: center; padding: 30px; color: #666;">
                                Nessun articolo presente
                            </td>
                        </tr>
            """
        
        # Calcoli finali
        ore_manodopera = float(mpls_data.get('ore_manodopera', 0))
        costo_orario = 25.0
        costo_manodopera = ore_manodopera * costo_orario
        sovrapprezzo = float(mpls_data.get('sovrapprezzo', 0))
        
        totale_netto = totale_vendita + costo_manodopera + sovrapprezzo
        margine = totale_netto - totale_costi - costo_manodopera
        margine_percentuale = (margine / totale_netto * 100) if totale_netto > 0 else 0
        
        html += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="calculations-section">
                <h3>CALCOLI E MARGINI</h3>
                <div class="calculations-grid">
                    <div class="calc-item">
                        <span class="calc-label">Totale Costi Materiali:</span>
                        <span class="calc-value">€ {totale_costi:.2f}</span>
                    </div>
                    <div class="calc-item">
                        <span class="calc-label">Ore Manodopera:</span>
                        <span class="calc-value">{ore_manodopera} ore</span>
                    </div>
                    <div class="calc-item">
                        <span class="calc-label">Costo Manodopera:</span>
                        <span class="calc-value">€ {costo_manodopera:.2f}</span>
                    </div>
                    <div class="calc-item">
                        <span class="calc-label">Sovrapprezzo:</span>
                        <span class="calc-value">€ {sovrapprezzo:.2f}</span>
                    </div>
                    <div class="calc-item total-item">
                        <span class="calc-label">TOTALE PREVENTIVO:</span>
                        <span class="calc-value">€ {totale_netto:.2f}</span>
                    </div>
                    <div class="calc-item margin-item">
                        <span class="calc-label">MARGINE:</span>
                        <span class="calc-value">€ {margine:.2f} ({margine_percentuale:.1f}%)</span>
                    </div>
                </div>
            </div>
            
            <div class="document-footer">
                <p>Documento generato automaticamente il {current_date}</p>
                <p>Sistema Gestione MPLS - {DocumentTemplate.COMPANY_DATA['ragione_sociale']}</p>
            </div>
            
            <div class="no-print" style="margin-top: 30px; text-align: center;">
                <button onclick="window.print()" class="print-btn">🖨️ Stampa</button>
                <button onclick="window.close()" class="close-btn">❌ Chiudi</button>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return DocumentTemplate.get_styles() + """
        .description-section { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .calculations-section { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .calculations-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
        .calc-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ddd; }
        .calc-label { font-weight: bold; }
        .calc-value { font-weight: bold; color: #003366; }
        .total-item { background: #e3f2fd; padding: 12px; border-radius: 5px; font-size: 1.1em; border: none; }
        .margin-item { background: #c8e6c9; padding: 12px; border-radius: 5px; font-size: 1.1em; border: none; }
        .print-btn, .close-btn { padding: 10px 20px; margin: 0 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .print-btn { background: #003366; color: white; }
        .close-btn { background: #666; color: white; }
        @media print { .no-print { display: none !important; } }
        """


class PreventivoTemplate(DocumentTemplate):
    """Template per Preventivi"""
    
    @staticmethod
    def generate_html(preventivo_data):
        """Genera HTML per Preventivo"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>Preventivo - {preventivo_data.get('numero', 'N/A')}</title>
            <style>{PreventivoTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>PREVENTIVO</h1>
                <div class="document-number">Preventivo N. {preventivo_data.get('numero', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>CLIENTE</h3>
                    <p><strong>{preventivo_data.get('cliente', 'N/A')}</strong></p>
                    <p>Data: {preventivo_data.get('data_creazione', current_date)}</p>
                    <p>Validità: {preventivo_data.get('validita_giorni', 30)} giorni</p>
                </div>
                
                <div class="section">
                    <h3>OGGETTO</h3>
                    <p>{preventivo_data.get('oggetto', 'Fornitura e installazione impianto climatizzazione')}</p>
                    <p>Stato: {preventivo_data.get('stato', 'BOZZA').upper()}</p>
                </div>
            </div>
            
            <div class="services-table">
                <h3>DETTAGLIO LAVORI/FORNITURE</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Descrizione</th>
                            <th>Quantità</th>
                            <th>U.M.</th>
                            <th>Prezzo Unit.</th>
                            <th>Sconto %</th>
                            <th>Totale</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        # Genera righe articoli dinamicamente
        if preventivo_data.get('articoli'):
            for articolo in preventivo_data['articoli']:
                html += f"""
                        <tr>
                            <td>{articolo.get('descrizione', 'N/A')}</td>
                            <td>{articolo.get('quantita', 0)}</td>
                            <td>{articolo.get('unita_misura', 'PZ')}</td>
                            <td>€ {articolo.get('prezzo_unitario', 0):.2f}</td>
                            <td>{articolo.get('sconto_percentuale', 0):.0f}%</td>
                            <td>€ {articolo.get('totale', 0):.2f}</td>
                        </tr>"""
        else:
            # Fallback se non ci sono articoli
            html += """
                        <tr>
                            <td colspan="6" style="text-align: center; color: #666; font-style: italic;">
                                Nessun articolo presente in questo preventivo
                            </td>
                        </tr>"""
        
        html += """
                    </tbody>
                    <tfoot>
                        <tr><td colspan="5">Subtotale:</td><td>€ """ + f"{preventivo_data.get('totale_netto', 0):.2f}" + """</td></tr>
                        <tr><td colspan="5">IVA """ + f"{preventivo_data.get('iva_percentuale', 22):.0f}" + """%:</td><td>€ """ + f"{(preventivo_data.get('totale_lordo', 0) - preventivo_data.get('totale_netto', 0)):.2f}" + """</td></tr>
                        <tr class="total-row"><td colspan="5"><strong>TOTALE PREVENTIVO:</strong></td><td><strong>€ """ + f"{preventivo_data.get('totale_lordo', 0):.2f}" + """</strong></td></tr>
                    </tfoot>
                </table>
            </div>
            
            <div class="document-footer">
                <p>Documento generato automaticamente il {current_date}</p>
                <p>Sistema Gestione DDT - {DocumentTemplate.COMPANY_DATA['ragione_sociale']}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return DocumentTemplate.get_styles() + """
        .services-table { margin: 30px 0; }
        """


class RichiestaOffertaTemplate(DocumentTemplate):
    """Template per Richieste di Offerta ai Fornitori"""
    
    @staticmethod
    def generate_html(offerta_data):
        """Genera HTML per Richiesta Offerta"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>Richiesta Offerta - {offerta_data.get('numero_offerta', 'N/A')}</title>
            <style>{RichiestaOffertaTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>RICHIESTA DI OFFERTA</h1>
                <div class="document-number">Richiesta N. {offerta_data.get('numero_offerta', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>FORNITORE DESTINATARIO</h3>
                    <p><strong>{offerta_data.get('fornitore_nome', 'N/A')}</strong></p>
                    <p>Data Richiesta: {offerta_data.get('data_offerta', current_date)}</p>
                    <p>Oggetto: {offerta_data.get('oggetto', 'Richiesta preventivo')}</p>
                </div>
                
                <div class="section">
                    <h3>CLIENTE FINALE</h3>
                    <p>Cliente: {offerta_data.get('cliente_nome', 'N/A')}</p>
                    <p>Commessa: {offerta_data.get('commessa', 'N/A')}</p>
                    <p>Priorità: {offerta_data.get('priorita', 'Media').upper()}</p>
                </div>
            </div>
            
            <div class="request-content">
                <h3>DETTAGLI RICHIESTA</h3>
                <div class="content-section">
                    <p>Gentili Signori,</p>
                    <p>Con la presente richiediamo un preventivo per la fornitura degli articoli sotto elencati:</p>
                </div>
            </div>
            
            <div class="articles-table">
                <h3>ARTICOLI RICHIESTI</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Codice</th>
                            <th>Descrizione</th>
                            <th>Quantità</th>
                            <th>U.M.</th>
                            <th>Note</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Aggiungi articoli richiesti
        if 'articoli' in offerta_data and offerta_data['articoli']:
            for articolo in offerta_data['articoli']:
                html += f"""
                        <tr>
                            <td>{articolo.get('codice_articolo', 'N/A')}</td>
                            <td><strong>{articolo.get('descrizione', 'N/A')}</strong></td>
                            <td>{articolo.get('quantita', 0)}</td>
                            <td>{articolo.get('unita_misura', 'PZ')}</td>
                            <td>{articolo.get('note', '')}</td>
                        </tr>
                """
        else:
            html += """
                        <tr>
                            <td colspan="5" style="text-align: center; padding: 30px; color: #666;">
                                Nessun articolo specificato - Richiesta generica
                            </td>
                        </tr>
            """
        
        html += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="request-conditions">
                <h3>CONDIZIONI RICHIESTE</h3>
                <div class="conditions-grid">
                    <div><strong>Tempi di consegna:</strong> Da specificare nell'offerta</div>
                    <div><strong>Disponibilità:</strong> Da confermare</div>
                    <div><strong>Validità offerta:</strong> Minimo 30 giorni</div>
                    <div><strong>Condizioni pagamento:</strong> Da concordare</div>
                </div>
                
                {f'<div class="notes"><strong>Note aggiuntive:</strong><p>{offerta_data.get("note", "")}</p></div>' if offerta_data.get("note") else ""}
            </div>
            
            <div class="response-section">
                <h3>MODALITÀ DI RISPOSTA</h3>
                <p>Vi preghiamo di inviarci la vostra migliore offerta entro i tempi concordati, specificando:</p>
                <ul>
                    <li>Prezzo unitario per ogni articolo</li>
                    <li>Sconti applicabili</li>
                    <li>Tempi di consegna</li>
                    <li>Disponibilità merce</li>
                    <li>Condizioni di pagamento</li>
                    <li>Validità dell'offerta</li>
                </ul>
            </div>
            
            <div class="document-footer">
                <div class="signature-section">
                    <p><strong>Cordiali saluti,</strong></p>
                    <p><strong>{DocumentTemplate.COMPANY_DATA['ragione_sociale']}</strong><br>
                       {DocumentTemplate.COMPANY_DATA['indirizzo']}<br>
                       {DocumentTemplate.COMPANY_DATA['cap']} {DocumentTemplate.COMPANY_DATA['citta']}</p>
                    <br>
                    <div class="signature-line">______________________</div>
                    <p><em>Firma autorizzata</em></p>
                </div>
                <p class="generated-date">Documento generato automaticamente il {current_date}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return DocumentTemplate.get_styles() + """
        .request-content { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .content-section p { margin: 10px 0; line-height: 1.6; }
        .request-conditions { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .conditions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }
        .notes { margin-top: 15px; padding: 15px; background: #fff; border-left: 4px solid #003366; }
        .response-section { margin: 30px 0; }
        .response-section ul { margin: 15px 0; padding-left: 25px; }
        .response-section li { margin: 8px 0; line-height: 1.4; }
        .signature-section { text-align: right; margin: 40px 0 20px 0; }
        .signature-line { border-bottom: 1px solid #333; width: 200px; margin: 20px 0 10px auto; }
        .generated-date { text-align: center; font-size: 12px; color: #666; margin-top: 30px; }
        """


class OrdineFornitoreTemplate(DocumentTemplate):
    """Template per Ordini a Fornitori"""
    
    @staticmethod
    def generate_html(ordine_data):
        """Genera HTML per Ordine Fornitore"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <title>Ordine - {ordine_data.get('numero', 'N/A')}</title>
            <style>{OrdineFornitoreTemplate.get_styles()}</style>
        </head>
        <body>
            {DocumentTemplate.get_header_company()}
            
            <div class="document-title">
                <h1>ORDINE DI ACQUISTO</h1>
                <div class="document-number">Ordine N. {ordine_data.get('numero', 'N/A')}</div>
            </div>
            
            <div class="document-details">
                <div class="section">
                    <h3>FORNITORE</h3>
                    <p><strong>{ordine_data.get('fornitore', 'N/A')}</strong></p>
                    <p>Data Ordine: {ordine_data.get('data_ordine', current_date)}</p>
                    <p>Riferimento: {ordine_data.get('riferimento', 'N/A')}</p>
                    <p>Numero Offerta: {ordine_data.get('numero_offerta_fornitore', 'N/A')}</p>
                    <p>Data Offerta: {ordine_data.get('data_offerta_fornitore', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h3>CONSEGNA</h3>
                    <p>Destinazione: {DocumentTemplate.COMPANY_DATA['indirizzo']}<br>
                       {DocumentTemplate.COMPANY_DATA['cap']} {DocumentTemplate.COMPANY_DATA['citta']}</p>
                    <p>Data richiesta: {ordine_data.get('data_consegna', 'Da concordare')}</p>
                    <p>Stato: {ordine_data.get('stato', 'EMESSO').upper()}</p>
                </div>
            </div>
            
            <div class="articles-table">
                <h3>ARTICOLI ORDINATI</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Codice</th>
                            <th>Descrizione</th>
                            <th>Quantità</th>
                            <th>U.M.</th>
                            <th>Prezzo Unit.</th>
                            <th>Sconto %</th>
                            <th>Totale</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="7" style="text-align: center; padding: 30px; color: #666;">
                                Articoli da implementare tramite relazioni Ordine-Articoli
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="order-conditions">
                <h3>CONDIZIONI DI FORNITURA</h3>
                <div class="conditions-grid">
                    <div><strong>Pagamento:</strong> {ordine_data.get('condizioni_pagamento', '30 gg fm')}</div>
                    <div><strong>Trasporto:</strong> Franco destinazione</div>
                    <div><strong>Imballo:</strong> A carico del fornitore</div>
                    <div><strong>Consegna:</strong> Come da accordi telefonici</div>
                </div>
            </div>
            
            <div class="document-footer">
                <div class="signature">
                    <p><strong>ACG CLIMA SERVICE S.R.L.</strong><br><br>
                       Firma autorizzata<br><br>
                       _______________________</p>
                </div>
                <p>Documento generato automaticamente il {current_date}</p>
                <p>Sistema Gestione DDT - {DocumentTemplate.COMPANY_DATA['ragione_sociale']}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_styles():
        return DocumentTemplate.get_styles() + """
        .order-conditions { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .conditions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }
        .signature { text-align: right; margin: 40px 0 20px 0; }
        """


# Funzioni di utilità per generare documenti
def generate_ddt_in_pdf(ddt_data):
    """Genera PDF per DDT IN"""
    html_content = DDTInTemplate.generate_html(ddt_data)
    # Qui si può integrare una libreria come weasyprint o pdfkit
    return html_content


def generate_ddt_out_pdf(ddt_data):
    """Genera PDF per DDT OUT"""
    html_content = DDTOutTemplate.generate_html(ddt_data)
    return html_content


def generate_preventivo_pdf(preventivo_data):
    """Genera PDF per Preventivo"""
    html_content = PreventivoTemplate.generate_html(preventivo_data)
    return html_content


def generate_ordine_fornitore_pdf(ordine_data):
    """Genera PDF per Ordine Fornitore"""
    html_content = OrdineFornitoreTemplate.generate_html(ordine_data)
    return html_content