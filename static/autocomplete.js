/**
 * Sistema di autocompletamento unificato per ACG Clima Service
 * Supporta ricerca testuale con filtro in tempo reale
 */

class Autocomplete {
    constructor(inputElement, options) {
        this.input = inputElement;
        this.options = {
            endpoint: options.endpoint,
            searchParam: options.searchParam || 'q',
            minChars: options.minChars || 2,
            displayKey: options.displayKey || 'nome',
            valueKey: options.valueKey || 'id',
            template: options.template || this.defaultTemplate,
            onSelect: options.onSelect || this.defaultOnSelect,
            placeholder: options.placeholder || 'Digita per cercare...',
            ...options
        };
        
        this.suggestionsList = null;
        this.timeout = null;
        this.cache = new Map();
        
        this.init();
    }
    
    init() {
        // Imposta placeholder
        this.input.placeholder = this.options.placeholder;
        
        // Crea contenitore suggerimenti
        this.createSuggestionsContainer();
        
        // Event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Chiudi suggerimenti cliccando altrove
        document.addEventListener('click', (e) => {
            if (!e.target.closest(`.autocomplete-container-${this.input.name}`)) {
                this.hideSuggestions();
            }
        });
    }
    
    createSuggestionsContainer() {
        // Wrappa input in container relativo se necessario
        if (!this.input.parentElement.classList.contains('autocomplete-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'autocomplete-wrapper';
            wrapper.style.position = 'relative';
            this.input.parentElement.insertBefore(wrapper, this.input);
            wrapper.appendChild(this.input);
        }
        
        // Crea lista suggerimenti
        this.suggestionsList = document.createElement('div');
        this.suggestionsList.className = `autocomplete-suggestions autocomplete-container-${this.input.name}`;
        this.suggestionsList.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        `;
        
        this.input.parentElement.appendChild(this.suggestionsList);
    }
    
    handleInput(e) {
        clearTimeout(this.timeout);
        const query = e.target.value.trim();
        
        if (query.length < this.options.minChars) {
            this.hideSuggestions();
            return;
        }
        
        this.timeout = setTimeout(() => {
            this.search(query);
        }, 300);
    }
    
    handleFocus(e) {
        const query = e.target.value.trim();
        if (query.length >= this.options.minChars) {
            this.search(query);
        }
    }
    
    handleBlur(e) {
        // Delay per permettere click su suggerimenti
        setTimeout(() => {
            if (!this.suggestionsList.matches(':hover')) {
                this.hideSuggestions();
            }
        }, 150);
    }
    
    handleKeydown(e) {
        const suggestions = this.suggestionsList.querySelectorAll('.suggestion-item');
        const current = this.suggestionsList.querySelector('.suggestion-item.selected');
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (!current) {
                    suggestions[0]?.classList.add('selected');
                } else {
                    current.classList.remove('selected');
                    const next = current.nextElementSibling || suggestions[0];
                    next.classList.add('selected');
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (!current) {
                    suggestions[suggestions.length - 1]?.classList.add('selected');
                } else {
                    current.classList.remove('selected');
                    const prev = current.previousElementSibling || suggestions[suggestions.length - 1];
                    prev.classList.add('selected');
                }
                break;
                
            case 'Enter':
                e.preventDefault();
                if (current) {
                    current.click();
                }
                break;
                
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }
    
    async search(query) {
        // Controlla cache
        const cacheKey = query.toLowerCase();
        if (this.cache.has(cacheKey)) {
            this.showSuggestions(this.cache.get(cacheKey), query);
            return;
        }
        
        try {
            const url = new URL(this.options.endpoint, window.location.origin);
            url.searchParams.append(this.options.searchParam, query);
            
            const response = await fetch(url);
            const data = await response.json();
            
            // Salva in cache
            this.cache.set(cacheKey, data);
            
            this.showSuggestions(data, query);
        } catch (error) {
            console.error('Errore ricerca autocomplete:', error);
            this.hideSuggestions();
        }
    }
    
    showSuggestions(items, query) {
        this.suggestionsList.innerHTML = '';
        
        if (!items || items.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'suggestion-item no-results';
            noResults.style.cssText = 'padding: 10px; color: #666; font-style: italic;';
            noResults.textContent = 'Nessun risultato trovato';
            this.suggestionsList.appendChild(noResults);
            this.suggestionsList.style.display = 'block';
            return;
        }
        
        items.forEach((item, index) => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = 'suggestion-item';
            suggestionDiv.style.cssText = `
                padding: 10px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                transition: background-color 0.2s;
            `;
            
            // Usa template personalizzato o default
            suggestionDiv.innerHTML = this.options.template(item, query);
            
            // Eventi hover
            suggestionDiv.addEventListener('mouseenter', () => {
                this.suggestionsList.querySelectorAll('.suggestion-item').forEach(s => s.classList.remove('selected'));
                suggestionDiv.classList.add('selected');
                suggestionDiv.style.backgroundColor = '#f0f0f0';
            });
            
            suggestionDiv.addEventListener('mouseleave', () => {
                suggestionDiv.style.backgroundColor = 'white';
            });
            
            // Click per selezione
            suggestionDiv.addEventListener('click', () => {
                this.selectItem(item);
            });
            
            this.suggestionsList.appendChild(suggestionDiv);
        });
        
        this.suggestionsList.style.display = 'block';
    }
    
    selectItem(item) {
        // Imposta valore input
        this.input.value = item[this.options.displayKey] || item.nome || item.ragione_sociale || '';
        
        // Imposta valore hidden se specificato
        if (this.options.hiddenInput) {
            const hiddenInput = document.querySelector(this.options.hiddenInput);
            if (hiddenInput) {
                hiddenInput.value = item[this.options.valueKey] || item.id || '';
            }
        }
        
        // Callback personalizzato
        this.options.onSelect(item, this.input);
        
        // Nascondi suggerimenti
        this.hideSuggestions();
        
        // Trigger change event
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    hideSuggestions() {
        this.suggestionsList.style.display = 'none';
        this.suggestionsList.querySelectorAll('.suggestion-item').forEach(s => s.classList.remove('selected'));
    }
    
    defaultTemplate(item, query) {
        const name = item.nome || item.ragione_sociale || item.descrizione || '';
        const highlight = this.highlightMatch(name, query);
        let details = '';
        
        if (item.partita_iva || item.codice_fiscale) {
            details += `<small style="color: #666;">`;
            if (item.partita_iva) details += `P.IVA: ${item.partita_iva}`;
            if (item.codice_fiscale && item.partita_iva) details += ` - `;
            if (item.codice_fiscale && !item.partita_iva) details += `CF: ${item.codice_fiscale}`;
            if (item.citta) details += ` - ${item.citta}`;
            details += `</small>`;
        } else if (item.codice) {
            details = `<small style="color: #666;">Codice: ${item.codice}</small>`;
        } else if (item.cliente_nome) {
            details = `<small style="color: #666;">Cliente: ${item.cliente_nome}</small>`;
        }
        
        return `<strong>${highlight}</strong>${details ? '<br>' + details : ''}`;
    }
    
    highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark style="background: #fff3cd;">$1</mark>');
    }
    
    defaultOnSelect(item, input) {
        // Override in options se necessario
    }
}

// Factory functions per tipi comuni
window.AutocompleteHelpers = {
    // Clienti
    setupClientiAutocomplete: function(inputElement, options = {}) {
        return new Autocomplete(inputElement, {
            endpoint: '/api/clienti/search',
            placeholder: 'Digita nome cliente...',
            displayKey: 'ragione_sociale',
            template: (item, query) => {
                const name = window.AutocompleteHelpers.highlightMatch(item.ragione_sociale, query);
                let details = '';
                if (item.partita_iva || item.citta) {
                    details = '<small style="color: #666;">';
                    if (item.partita_iva) details += `P.IVA: ${item.partita_iva}`;
                    if (item.citta) details += `${item.partita_iva ? ' - ' : ''}${item.citta}`;
                    details += '</small>';
                }
                return `<strong>${name}</strong>${details ? '<br>' + details : ''}`;
            },
            ...options
        });
    },
    
    // Fornitori  
    setupFornitoriAutocomplete: function(inputElement, options = {}) {
        return new Autocomplete(inputElement, {
            endpoint: '/api/fornitori/search',
            placeholder: 'Digita nome fornitore...',
            displayKey: 'ragione_sociale',
            template: (item, query) => {
                const name = window.AutocompleteHelpers.highlightMatch(item.ragione_sociale, query);
                let details = '';
                if (item.partita_iva || item.citta) {
                    details = '<small style="color: #666;">';
                    if (item.partita_iva) details += `P.IVA: ${item.partita_iva}`;
                    if (item.citta) details += `${item.partita_iva ? ' - ' : ''}${item.citta}`;
                    details += '</small>';
                }
                return `<strong>${name}</strong>${details ? '<br>' + details : ''}`;
            },
            ...options
        });
    },
    
    // Commesse
    setupCommesseAutocomplete: function(inputElement, options = {}) {
        return new Autocomplete(inputElement, {
            endpoint: '/api/commesse/search',
            placeholder: 'Digita numero o descrizione commessa...',
            displayKey: 'display_name',
            template: (item, query) => {
                const number = window.AutocompleteHelpers.highlightMatch(item.numero_progressivo, query);
                const desc = item.descrizione ? window.AutocompleteHelpers.highlightMatch(item.descrizione.substring(0, 50), query) : '';
                return `<strong>Commessa ${number}</strong><br><small style="color: #666;">${item.cliente_nome} - ${desc}${item.descrizione && item.descrizione.length > 50 ? '...' : ''}</small>`;
            },
            onSelect: (item, input) => {
                input.value = `Commessa ${item.numero_progressivo}`;
            },
            ...options
        });
    },
    
    // Articoli
    setupArticoliAutocomplete: function(inputElement, options = {}) {
        return new Autocomplete(inputElement, {
            endpoint: '/api/articoli/search',
            placeholder: 'Digita per cercare articolo...',
            displayKey: 'descrizione',
            template: (item, query) => {
                const codiceInterno = item.codice_interno || '';
                const codiceFornitore = item.codice_fornitore || '';
                const desc = window.AutocompleteHelpers.highlightMatch(item.descrizione, query);
                const dettagli = [];
                
                if (codiceInterno) dettagli.push(`Cod: ${codiceInterno}`);
                if (codiceFornitore) dettagli.push(`Forn: ${codiceFornitore}`);
                if (item.fornitore_principale) dettagli.push(item.fornitore_principale);
                
                const dettagliText = dettagli.length > 0 ? dettagli.join(' - ') : '';
                
                return `<strong>${desc}</strong>${dettagliText ? '<br><small style="color: #666;">' + dettagliText + '</small>' : ''}`;
            },
            onSelect: (item, input) => {
                input.value = item.descrizione;
                
                // Trova la riga corrente
                const riga = input.closest('.dettaglio-riga, .dettaglio-row');
                if (riga) {
                    // Cerca i campi codice nella stessa riga
                    const codiceInternoField = riga.querySelector('input[name*="[codice_interno]"], input[name*="[codice]"]');
                    const codiceFornitoreField = riga.querySelector('input[name*="[codice_fornitore]"]');
                    
                    // Imposta i valori
                    if (codiceInternoField && item.codice_interno) {
                        codiceInternoField.value = item.codice_interno;
                    }
                    if (codiceFornitoreField && item.codice_fornitore) {
                        codiceFornitoreField.value = item.codice_fornitore;
                    }
                }
            },
            ...options
        });
    },

    // Mastrini
    setupMastriniAutocomplete: function(inputElement, tipo = null, options = {}) {
        const endpoint = '/api/mastrini/search';
        const placeholder = tipo ? 
            `Digita mastrino ${tipo.toLowerCase()}...` : 
            'Digita codice o descrizione mastrino...';
            
        return new Autocomplete(inputElement, {
            endpoint: endpoint + (tipo ? `?tipo=${tipo}` : ''),
            placeholder: placeholder,
            displayKey: 'descrizione',
            template: (item, query) => {
                const code = window.AutocompleteHelpers.highlightMatch(item.codice, query);
                const desc = window.AutocompleteHelpers.highlightMatch(item.descrizione, query);
                return `<strong>${code}</strong><br><small style="color: #666;">${desc}</small>`;
            },
            onSelect: (item, input) => {
                input.value = `${item.codice} - ${item.descrizione}`;
            },
            ...options
        });
    },
    
    // Helper per evidenziare match
    highlightMatch: function(text, query) {
        if (!text || !query) return text || '';
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark style="background: #fff3cd;">$1</mark>');
    }
};

// CSS per autocomplete (aggiunto dinamicamente)
const autocompleteCSS = `
.autocomplete-wrapper {
    position: relative;
}

.autocomplete-suggestions .suggestion-item:last-child {
    border-bottom: none;
}

.autocomplete-suggestions .suggestion-item.selected {
    background-color: #f0f0f0 !important;
}

.autocomplete-suggestions .no-results {
    cursor: default !important;
}

.autocomplete-suggestions mark {
    background: #fff3cd !important;
    padding: 1px 2px;
    border-radius: 2px;
}
`;

// Aggiungi CSS se non presente
if (!document.getElementById('autocomplete-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'autocomplete-styles';
    styleSheet.textContent = autocompleteCSS;
    document.head.appendChild(styleSheet);
}