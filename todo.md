1\. nell'inventario non è valorizzato il campo ubicazione. **FATTO** ✅

* Aggiunta colonna Ubicazione nella tabella inventario
* Campo ubicazione mostrato correttamente dal database
* Aggiunto fallback "Non specificata" per articoli senza ubicazione
* Aggiunte statistiche inventario con valore totale, numero articoli, pezzi totali
* Aggiunto indicatore per articoli sotto scorta
* Migliorato layout con stati colorati (Disponibile, Sotto scorta, Esaurito)
* 2\. nella creazione manuale del ddt in e nell'importazione del ddt in aggiungere la colonna unità di misura. Per gli articoli con Unità di Misura (UM) "pz" (pezzi), il campo quantità non deve accettare valori decimali. **FATTO** ✅ *18:51 24-08-2025*
  - Aggiunta colonna "Unità Misura" con opzioni: PZ, KG, MT, LT, MQ, MC
  - Implementato controllo automatico decimali per articoli "PZ" 
  - Aggiornato form creazione manuale e modifica dati PDF
  - Validazione JavaScript per arrotondamento automatico quantità pezzi
* 3\. l'inventario deve riportare anche le giacenze negative in caso di vendita in eccesso creando i ddt out. **FATTO** ✅ *18:56 24-08-2025*
  - Modifica calcolo statistiche per includere articoli con giacenza ≠ 0 (anche negative)
  - Aggiunto stato "Negativo" in rosso per giacenze < 0  
  - Aggiunta card statistica "Giacenze Negative" nell'inventario
  - Migliorata visualizzazione stati: Negativo, Esaurito, Sotto scorta, Disponibile
* 4\. Le liste documenti dei ddt in e dei ddt out devono essere ordinate di default per numero documento in ordine crescente. Implementare un controllo per prevenire "buchi" nella numerazione sequenziale.
* 5\.  nella sezione ddt out implementare un box di ricerca  (per capirci come  quella della sezione ddt in)
* 6\. nella lista documenti dei ddt out aggiungi un opzione per la stampa di ogni signolo ddt out
* 7\. nella sezione catalogo aggiungere un box di ricerca 
* 8\. nella sezione movimenti aggiungi un box di ricerca 
* 9\. nelle sezioni clienti e fornitori non funziona il tasto modifica per le anagrafiche già create.
* 10\. nella sezione impostazioni aggiungere la possibilità di creare nuovi mastrini ricavi e nuovi mastrini acquisti
* 11\. Movimenti Interni: Introdurre una nuova tipologia di documento per la gestione dei "Movimenti Interni", che permetta di tracciare lo spostamento di materiale da un magazzino all'altro.
* 12\. Collegamento Mastrini: Nelle impostazioni, creare una funzionalità per collegare logicamente i mastrini di acquisto a quelli di vendita 
* 13\.  Report per Mastrini: Creare una nuova sezione di reportistica che permetta di visualizzare i totali di spesa e ricavo, aggregati per mastrino di acquisto e di vendita.
* 14\.  Gestione Commesse: Creare una nuova sezione dedicata alla gestione delle "Commesse". Ogni commessa deve avere i seguenti campi:
* Numero progressivo.
* Data di apertura.
* Stato (es. Aperta, Chiusa).
* Cliente associato.
* Tipologia (es. Riqualificazione, Manutenzione Ordinaria, Manutenzione Straordinaria).
* Possibilità di collegare DDT IN e DDT OUT specifici.
* 15\. Nell'inventario, visualizzare il mastrino d'acquisto per ogni articolo, duplicando la riga se un articolo ha giacenze associate a mastrini d'acquisto diversi.
* 16\. Automazione Creazione Fornitore: Implementare una logica per cui, durante l'importazione di un DDT in da PDFo la creazione manuale del ddt in, il sistema proponga la creazione di una nuova anagrafica fornitore se non esistente, pre-compilando i dati estratti in caso di importazione del pdf. Prevedere un controllo per evitare la creazione di duplicati.
* 17\.  nella sezione movimenti aggiungere le colonne di provenienza ("DA") e destinazione ("A"). La logica è la seguente: quanto ho un movimento in entrata la provenienza deve riportare il fornitore e la destinazione il magazzino di destinazione, mentre quando ho un movimento in uscita la provenienza deve riportare il magazzino e la destinazione il cliente. 
