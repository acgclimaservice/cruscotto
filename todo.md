1 crea i modelli per i ddt in ddt put, preventivi e ordini fornitori, l'intestazione è la notra ditta acg clima service trova i dati in rete
**FATTO** - Creati template completi per tutti i documenti con dati ACG CLIMA SERVICE S.R.L. (Alessandria)

2 dovresti già avere nel codice la lista di tutti i mastrini
**FATTO** - Sistema mastrini completamente implementato con pagina di gestione

3 tutte le pagine tranne dashboard devono avere solo il tasto che rimanda a dashboard, la pagina dashboard invece lasciala così
**FATTO** - Aggiornati 12/13 template per avere solo il link alla dashboard nella navigazione

4 quando scansioni un pdf, dammi una finestra del file pdf scansionato evidenziando in trasparenza i dati estratti sul pdf originale
**FATTO** - Implementato visualizzatore PDF completo con:
- Estrazione coordinate con pdfplumber
- Conversione PDF in immagine con PyMuPDF  
- Overlay trasparente con highlighting colorato dei campi estratti
- Leggenda colori e tooltip informativi
- Supporto Dual AI (Claude + Gemini) per massima accuratezza
- Endpoint API: /api/parsing/parse-pdf-highlight

5 nella pagina ddt in non funziona il tasto visualizza
**FATTO** - Aggiunte route mancanti:
- /ddt/in/{id} per visualizzare singolo DDT IN
- /ddt/out/{id} per visualizzare singolo DDT OUT  
- /ddt/in/nuovo per creare nuovo DDT IN
- /ddt/out/nuovo per creare nuovo DDT OUT

