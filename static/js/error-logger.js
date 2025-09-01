/**
 * JavaScript Error Logger - Cattura errori JSON e li invia al server
 */

// Intercetta tutti gli errori JavaScript
window.addEventListener('error', function(event) {
    const errorInfo = {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error ? event.error.toString() : null,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
    };
    
    // Controlla se è un errore di parsing JSON
    if (errorInfo.message && errorInfo.message.toLowerCase().includes('json')) {
        console.error('🔍 JSON ERROR DETECTED:', errorInfo);
        sendErrorToServer('JSON_PARSE_ERROR', errorInfo);
    }
});

// Intercetta errori di parsing JSON in fetch
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    console.log('🔍 FETCH REQUEST:', url);
    
    return originalFetch.apply(this, args).then(response => {
        console.log('🔍 FETCH RESPONSE:', response.status, response.statusText, 'for', url);
        console.log('🔍 RESPONSE Content-Type:', response.headers.get('content-type'));
        
        // Intercetta chiamate .json()
        const originalJson = response.json;
        response.json = function() {
            return originalJson.call(this).catch(error => {
                console.error('🔍 JSON PARSE ERROR in fetch response:', error);
                console.error('🔍 URL was:', url);
                console.error('🔍 Response status:', response.status);
                console.error('🔍 Response headers:', Object.fromEntries(response.headers.entries()));
                
                // Leggi il body come testo per vedere cosa abbiamo ricevuto
                return response.text().then(text => {
                    console.error('🔍 Raw response text:', text);
                    sendErrorToServer('FETCH_JSON_PARSE_ERROR', {
                        url: url,
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        responseText: text,
                        parseError: error.toString(),
                        timestamp: new Date().toISOString()
                    });
                    throw error;
                });
            });
        };
        
        return response;
    });
};

// Funzione per inviare errori al server
function sendErrorToServer(errorType, errorData) {
    try {
        fetch('/api/log-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: errorType,
                data: errorData
            })
        }).catch(err => {
            console.error('Failed to send error to server:', err);
        });
    } catch (e) {
        console.error('Error sending error to server:', e);
    }
}

console.log('🔍 JavaScript error logger initialized');