// Autocompletamento per articoli e altre entità
class AutoComplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            endpoint: options.endpoint || '/api/articoli/search',
            minChars: options.minChars || 2,
            maxResults: options.maxResults || 10,
            onSelect: options.onSelect || null,
            placeholder: options.placeholder || 'Inizia a digitare...'
        };
        
        this.results = [];
        this.currentIndex = -1;
        this.dropdownOpen = false;
        
        this.init();
    }
    
    init() {
        // Crea container per risultati
        this.resultsContainer = document.createElement('div');
        this.resultsContainer.className = 'autocomplete-results';
        this.input.parentNode.appendChild(this.resultsContainer);
        
        // Event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        
        document.addEventListener('click', (e) => {
            if (!this.input.parentNode.contains(e.target)) {
                this.hideResults();
            }
        });
    }
    
    async handleInput(e) {
        const query = e.target.value.trim();
        
        if (query.length < this.options.minChars) {
            this.hideResults();
            return;
        }
        
        try {
            const response = await fetch(`${this.options.endpoint}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.results = data;
            this.showResults();
        } catch (error) {
            console.error('Errore autocompletamento:', error);
            this.hideResults();
        }
    }
    
    handleKeydown(e) {
        if (!this.dropdownOpen) return;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.currentIndex = Math.min(this.currentIndex + 1, this.results.length - 1);
                this.updateHighlight();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.currentIndex = Math.max(this.currentIndex - 1, -1);
                this.updateHighlight();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.currentIndex >= 0) {
                    this.selectResult(this.results[this.currentIndex]);
                }
                break;
                
            case 'Escape':
                this.hideResults();
                break;
        }
    }
    
    handleBlur(e) {
        // Ritarda la chiusura per permettere click sui risultati
        setTimeout(() => {
            if (!this.resultsContainer.contains(document.activeElement)) {
                this.hideResults();
            }
        }, 100);
    }
    
    handleFocus(e) {
        if (this.results.length > 0) {
            this.showResults();
        }
    }
    
    showResults() {
        if (this.results.length === 0) {
            this.hideResults();
            return;
        }
        
        this.resultsContainer.innerHTML = '';
        this.currentIndex = -1;
        
        this.results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerHTML = this.formatResult(result);
            
            item.addEventListener('click', () => {
                this.selectResult(result);
            });
            
            this.resultsContainer.appendChild(item);
        });
        
        this.resultsContainer.style.display = 'block';
        this.dropdownOpen = true;
    }
    
    hideResults() {
        this.resultsContainer.style.display = 'none';
        this.dropdownOpen = false;
        this.currentIndex = -1;
    }
    
    updateHighlight() {
        const items = this.resultsContainer.querySelectorAll('.autocomplete-item');
        
        items.forEach((item, index) => {
            if (index === this.currentIndex) {
                item.classList.add('highlighted');
            } else {
                item.classList.remove('highlighted');
            }
        });
    }
    
    formatResult(result) {
        // Override questo metodo per diversi tipi di risultati
        if (result.codice && result.descrizione) {
            return `
                <div class="autocomplete-main">${result.codice} - ${result.descrizione}</div>
                <div class="autocomplete-details">
                    ${result.prezzo ? `€ ${result.prezzo.toFixed(2)}` : ''} 
                    ${result.unita ? `(${result.unita})` : ''}
                </div>
            `;
        }
        
        return result.toString();
    }
    
    selectResult(result) {
        this.input.value = result.descrizione || result.toString();
        this.hideResults();
        
        if (this.options.onSelect) {
            this.options.onSelect(result);
        }
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        this.input.dispatchEvent(event);
    }
}

// Funzioni di utility per autocompletamento specifico

function initArticoliAutoComplete(inputElement, options = {}) {
    return new AutoComplete(inputElement, {
        endpoint: '/api/articoli/search',
        onSelect: (articolo) => {
            // Popola automaticamente altri campi se disponibili
            const row = inputElement.closest('.dettaglio-row');
            if (row) {
                const codiceInput = row.querySelector('[name*="[codice]"]');
                const prezzoInput = row.querySelector('[name*="[prezzo_unitario]"]');
                const costoInput = row.querySelector('[name*="[costo]"]');
                const unitaSelect = row.querySelector('[name*="[unita]"]');
                
                if (codiceInput && articolo.codice) {
                    codiceInput.value = articolo.codice;
                }
                
                if (prezzoInput && articolo.prezzo) {
                    prezzoInput.value = articolo.prezzo.toFixed(2);
                }
                
                if (costoInput && articolo.costo) {
                    costoInput.value = articolo.costo.toFixed(2);
                }
                
                if (unitaSelect && articolo.unita) {
                    unitaSelect.value = articolo.unita;
                }
                
                // Ricalcola totale riga
                const index = row.dataset.index;
                if (index !== undefined && typeof calcolaTotaleRiga === 'function') {
                    calcolaTotaleRiga(parseInt(index));
                }
            }
        },
        ...options
    });
}

// Inizializza autocompletamento quando il DOM è pronto
document.addEventListener('DOMContentLoaded', function() {
    // Autocompletamento per descrizioni articoli
    const articoliInputs = document.querySelectorAll('[name*="[descrizione]"]');
    articoliInputs.forEach(input => {
        if (input.closest('.dettaglio-row')) {
            initArticoliAutoComplete(input);
        }
    });
    
    // Reinizializza quando vengono aggiunte nuove righe
    document.addEventListener('nuovaRigaAggiunta', function(e) {
        const nuovaRiga = e.detail.riga;
        const descrizioneInput = nuovaRiga.querySelector('[name*="[descrizione]"]');
        if (descrizioneInput) {
            initArticoliAutoComplete(descrizioneInput);
        }
    });
});

// Funzioni per modal di conferma
function mostraModalConferma(titolo, messaggio, callback) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${titolo}</h3>
            <p>${messaggio}</p>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="chiudiModal()">Annulla</button>
                <button class="btn btn-danger" onclick="confermaAzione()">Conferma</button>
            </div>
        </div>
    `;
    
    // Store callback
    window.modalCallback = callback;
    
    document.body.appendChild(modal);
    window.currentModal = modal;
}

function mostraModalValutazione(offertaId) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>🔍 Valuta Offerta</h3>
            <form method="POST" action="/offerte/${offertaId}/valuta">
                <div class="form-group">
                    <label>Valutazione:</label>
                    <textarea name="valutazione" rows="4" placeholder="Inserisci la tua valutazione dell'offerta..." required></textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="chiudiModal()">Annulla</button>
                    <button type="submit" class="btn btn-warning">💾 Salva Valutazione</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentModal = modal;
}

function mostraModalRifiuto(type, id) {
    const isOfferta = type === 'offerta';
    const endpoint = isOfferta ? `/offerte/${id}/rifiuta` : `/preventivi/${id}/rifiuta`;
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>❌ Rifiuta ${isOfferta ? 'Offerta' : 'Preventivo'}</h3>
            <form method="POST" action="${endpoint}">
                ${isOfferta ? `
                <div class="form-group">
                    <label>Motivo del rifiuto:</label>
                    <textarea name="motivo" rows="3" placeholder="Inserisci il motivo del rifiuto (opzionale)"></textarea>
                </div>
                ` : ''}
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="chiudiModal()">Annulla</button>
                    <button type="submit" class="btn btn-danger">❌ Conferma Rifiuto</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentModal = modal;
}

function chiudiModal() {
    if (window.currentModal) {
        document.body.removeChild(window.currentModal);
        window.currentModal = null;
        window.modalCallback = null;
    }
}

function confermaAzione() {
    if (window.modalCallback) {
        window.modalCallback();
    }
    chiudiModal();
}