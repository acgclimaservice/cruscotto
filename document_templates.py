# document_templates.py
# Modelli per documenti DDT IN/OUT, Preventivi e Ordini
from datetime import datetime
from models import db

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
    def get_header_company():
        """Header comune con dati aziendali"""
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
                <div class="logo-placeholder">ACG</div>
            </div>
        </div>
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
        .document-header { display: flex; justify-content: space-between; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
        .company-info h2 { color: #007bff; margin: 0 0 10px 0; }
        .company-info p { margin: 2px 0; font-size: 14px; }
        .logo-placeholder { width: 80px; height: 80px; background: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; border-radius: 8px; }
        .document-title { text-align: center; margin: 30px 0; }
        .document-title h1 { color: #007bff; margin-bottom: 10px; }
        .document-number { background: #f8f9fa; padding: 10px; border-radius: 5px; font-weight: bold; }
        .document-details { display: flex; gap: 30px; margin: 30px 0; }
        .section { flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .section h3 { color: #007bff; margin-top: 0; }
        .articles-table { margin: 30px 0; }
        .articles-table h3 { color: #007bff; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #ddd; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #007bff; color: white; font-weight: bold; }
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
                        <tr>
                            <td colspan="6" style="text-align: center; padding: 30px; color: #666;">
                                Articoli da implementare tramite relazioni DDT-Articoli
                            </td>
                        </tr>
                    </tbody>
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
        return DDTInTemplate.get_styles() + """
        .transport-info { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .transport-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }
        .signatures { display: flex; justify-content: space-between; margin: 40px 0 20px 0; }
        .signatures div { text-align: center; }
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
                    <tbody>
                        <tr>
                            <td>Installazione impianto climatizzazione</td>
                            <td>1</td>
                            <td>SERV</td>
                            <td>€ 2.500,00</td>
                            <td>0%</td>
                            <td>€ 2.500,00</td>
                        </tr>
                        <tr>
                            <td>Fornitura materiali</td>
                            <td>1</td>
                            <td>LOT</td>
                            <td>€ 1.800,00</td>
                            <td>5%</td>
                            <td>€ 1.710,00</td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr><td colspan="5">Subtotale:</td><td>€ 4.210,00</td></tr>
                        <tr><td colspan="5">IVA 22%:</td><td>€ 926,20</td></tr>
                        <tr class="total-row"><td colspan="5"><strong>TOTALE PREVENTIVO:</strong></td><td><strong>€ 5.136,20</strong></td></tr>
                    </tfoot>
                </table>
            </div>
            
            <div class="conditions">
                <h3>CONDIZIONI</h3>
                <ul>
                    <li><strong>Pagamento:</strong> 30% all'ordine, saldo a consegna ultimata</li>
                    <li><strong>Consegna:</strong> 15-20 giorni lavorativi dalla conferma d'ordine</li>
                    <li><strong>Validità offerta:</strong> 30 giorni dalla data di emissione</li>
                    <li><strong>Garanzia:</strong> 24 mesi su materiali e installazione</li>
                    <li><strong>Assistenza:</strong> Contratto di manutenzione disponibile</li>
                </ul>
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
        return DDTInTemplate.get_styles() + """
        .services-table { margin: 30px 0; }
        .conditions { margin: 30px 0; background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .conditions ul { margin: 10px 0; padding-left: 20px; }
        .conditions li { margin: 8px 0; }
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
        return DDTInTemplate.get_styles() + """
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