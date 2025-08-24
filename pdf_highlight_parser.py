# pdf_highlight_parser.py
import json
import os
import base64
from datetime import datetime
from models import db, ConfigurazioneSistema
from multi_ai_pdf_parser import MultiAIPDFParser
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Import opzionali
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class PDFHighlightParser(MultiAIPDFParser):
    """Parser PDF che identifica le coordinate del testo estratto per evidenziazione"""
    
    def extract_text_with_coordinates(self, pdf_file):
        """Estrae testo dal PDF con coordinate per evidenziazione"""
        if not PDFPLUMBER_AVAILABLE:
            return self.extract_text_from_pdf(pdf_file), []
        
        try:
            # Reset file pointer
            pdf_file.seek(0)
            
            with pdfplumber.open(pdf_file) as pdf:
                full_text = ""
                coordinates_map = []
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                        
                        # Estrae coordinate delle parole
                        words = page.extract_words()
                        for word in words:
                            coordinates_map.append({
                                'text': word['text'],
                                'page': page_num,
                                'x0': word['x0'],
                                'y0': word['y0'],
                                'x1': word['x1'],
                                'y1': word['y1'],
                                'width': page.width,
                                'height': page.height
                            })
                
                return full_text, coordinates_map
                
        except Exception as e:
            print(f"Errore estrazione coordinate: {e}")
            # Fallback al metodo standard
            return self.extract_text_from_pdf(pdf_file), []
    
    def find_text_coordinates(self, search_text, coordinates_map):
        """Trova le coordinate di un testo specifico nel PDF"""
        if not search_text or not coordinates_map:
            return []
        
        matches = []
        search_words = search_text.lower().split()
        
        for i, word_data in enumerate(coordinates_map):
            word = word_data['text'].lower()
            
            # Cerca corrispondenza parola singola o inizio sequenza
            if word in search_words or search_words[0] in word:
                # Controlla se è l'inizio di una sequenza di parole
                match_coords = [word_data]
                matched_words = 1
                
                # Prova a trovare parole consecutive
                for j in range(i + 1, min(i + len(search_words), len(coordinates_map))):
                    next_word = coordinates_map[j]['text'].lower()
                    if matched_words < len(search_words) and search_words[matched_words] in next_word:
                        match_coords.append(coordinates_map[j])
                        matched_words += 1
                    else:
                        break
                
                # Se ha trovato abbastanza parole, aggiungi alla lista
                if matched_words >= min(2, len(search_words)):
                    matches.append({
                        'matched_text': ' '.join([w['text'] for w in match_coords]),
                        'coordinates': match_coords,
                        'confidence': matched_words / len(search_words)
                    })
        
        # Ordina per confidence e rimuovi duplicati
        matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
        unique_matches = []
        seen_texts = set()
        
        for match in matches:
            text_key = match['matched_text'].lower()
            if text_key not in seen_texts:
                unique_matches.append(match)
                seen_texts.add(text_key)
        
        return unique_matches[:5]  # Massimo 5 match per campo
    
    def create_highlight_data(self, parsed_data, coordinates_map):
        """Crea dati per evidenziare i campi estratti nel PDF"""
        highlight_data = {
            'highlights': [],
            'fields_found': 0,
            'total_fields': 0
        }
        
        # Campi da evidenziare
        fields_to_highlight = {
            'fornitore': {'color': '#ff6b6b', 'label': 'Fornitore'},
            'numero_ddt_origine': {'color': '#4ecdc4', 'label': 'Numero DDT'},
            'data_ddt_origine': {'color': '#45b7d1', 'label': 'Data DDT'},
            'destinazione': {'color': '#96ceb4', 'label': 'Destinazione'},
            'riferimento': {'color': '#feca57', 'label': 'Riferimento'}
        }
        
        highlight_data['total_fields'] = len(fields_to_highlight)
        
        for field_name, field_config in fields_to_highlight.items():
            field_value = parsed_data.get(field_name, '')
            
            if field_value and isinstance(field_value, str) and len(field_value.strip()) > 2:
                # Cerca coordinate per questo campo
                matches = self.find_text_coordinates(field_value, coordinates_map)
                
                if matches:
                    best_match = matches[0]  # Prende il match migliore
                    highlight_data['highlights'].append({
                        'field_name': field_name,
                        'field_label': field_config['label'],
                        'field_value': field_value,
                        'matched_text': best_match['matched_text'],
                        'coordinates': best_match['coordinates'],
                        'color': field_config['color'],
                        'confidence': best_match['confidence']
                    })
                    highlight_data['fields_found'] += 1
        
        # Evidenzia articoli se presenti
        if 'articoli' in parsed_data and parsed_data['articoli']:
            for idx, articolo in enumerate(parsed_data['articoli'][:3]):  # Max 3 articoli
                descrizione = articolo.get('descrizione', '')
                if descrizione and len(descrizione.strip()) > 3:
                    matches = self.find_text_coordinates(descrizione, coordinates_map)
                    if matches:
                        highlight_data['highlights'].append({
                            'field_name': f'articolo_{idx}',
                            'field_label': f'Articolo {idx + 1}',
                            'field_value': descrizione,
                            'matched_text': matches[0]['matched_text'],
                            'coordinates': matches[0]['coordinates'],
                            'color': '#e17055',
                            'confidence': matches[0]['confidence']
                        })
        
        return highlight_data
    
    def parse_pdf_with_highlights(self, pdf_file, learning_data=None, preferred_ai='dual'):
        """Parsing completo con dati per evidenziazione"""
        
        # Estrae testo e coordinate
        pdf_text, coordinates_map = self.extract_text_with_coordinates(pdf_file)
        
        if not pdf_text:
            return {
                'success': False,
                'error': 'Impossibile estrarre testo dal PDF'
            }
        
        # Parsing con AI
        parsed_data = self.parse_ddt_with_ai(pdf_text, learning_data, preferred_ai)
        
        if not parsed_data:
            return {
                'success': False,
                'error': 'Parsing fallito'
            }
        
        # Crea dati per evidenziazione
        highlight_data = self.create_highlight_data(parsed_data, coordinates_map)
        
        # Converte PDF in immagine per visualizzazione (opzionale)
        pdf_image_base64 = self.convert_pdf_to_image(pdf_file)
        
        return {
            'success': True,
            'parsed_data': parsed_data,
            'highlight_data': highlight_data,
            'pdf_image': pdf_image_base64,
            'coordinates_count': len(coordinates_map),
            'pages_processed': max([coord['page'] for coord in coordinates_map]) + 1 if coordinates_map else 0
        }
    
    def convert_pdf_to_image(self, pdf_file):
        """Converte la prima pagina del PDF in immagine base64 per visualizzazione"""
        if not PYMUPDF_AVAILABLE:
            return None
        
        try:
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            
            # Apri PDF con PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if len(doc) == 0:
                return None
            
            # Prende la prima pagina
            page = doc[0]
            
            # Converti in immagine con risoluzione moderata
            mat = fitz.Matrix(1.5, 1.5)  # Zoom 1.5x
            pix = page.get_pixmap(matrix=mat)
            
            # Converti in bytes PNG
            png_data = pix.tobytes("png")
            
            # Converti in base64
            pdf_image_base64 = base64.b64encode(png_data).decode('utf-8')
            
            doc.close()
            return f"data:image/png;base64,{pdf_image_base64}"
            
        except Exception as e:
            print(f"Errore conversione PDF in immagine: {e}")
            return None


# Funzione di utilità per il testing
def test_highlight_parsing():
    """Test del sistema di evidenziazione"""
    from app import app
    
    with app.app_context():
        parser = PDFHighlightParser()
        
        # Test con testo simulato
        test_text = """
        DDT N. 2024/003
        Data: 25/01/2024
        
        Fornitore: TechSupply Italia S.r.l.
        P.IVA: 11223344556
        
        Destinazione: Magazzino Centrale
        Via Roma 123, Milano
        
        Articoli:
        TS001    Server Dell PowerEdge    1 PZ    € 2400,00
        TS002    Switch Cisco 24 Port     2 PZ    € 380,00
        
        Totale: € 3160,00
        """
        
        print("=== TEST PARSING CON HIGHLIGHTING ===")
        print("Simulazione coordinate per test...")
        
        # Simula coordinate per testing
        fake_coordinates = [
            {'text': 'TechSupply', 'page': 0, 'x0': 100, 'y0': 200, 'x1': 180, 'y1': 220, 'width': 595, 'height': 842},
            {'text': 'Italia', 'page': 0, 'x0': 185, 'y0': 200, 'x1': 220, 'y1': 220, 'width': 595, 'height': 842},
            {'text': '2024/003', 'page': 0, 'x0': 300, 'y0': 150, 'x1': 360, 'y1': 170, 'width': 595, 'height': 842},
            {'text': 'Server', 'page': 0, 'x0': 50, 'y0': 400, 'x1': 90, 'y1': 420, 'width': 595, 'height': 842},
            {'text': 'Dell', 'page': 0, 'x0': 95, 'y0': 400, 'x1': 120, 'y1': 420, 'width': 595, 'height': 842}
        ]
        
        # Parse del testo
        parsed_data = parser.parse_ddt_with_ai(test_text, preferred_ai='claude')
        
        if parsed_data:
            print(f"Fornitore estratto: {parsed_data.get('fornitore', 'N/A')}")
            print(f"Numero DDT: {parsed_data.get('numero_ddt_origine', 'N/A')}")
            
            # Crea dati highlighting
            highlight_data = parser.create_highlight_data(parsed_data, fake_coordinates)
            
            print(f"\nHighlighting:")
            print(f"Campi trovati: {highlight_data['fields_found']}/{highlight_data['total_fields']}")
            
            for highlight in highlight_data['highlights']:
                print(f"- {highlight['field_label']}: {highlight['field_value']}")
                print(f"  Coordinate: {len(highlight['coordinates'])} parole")
                print(f"  Confidence: {highlight['confidence']:.2f}")
        
        print("\nSistema highlighting pronto per integrazione!")


if __name__ == "__main__":
    test_highlight_parsing()