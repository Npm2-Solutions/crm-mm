# Il design system di DottorCloud

Piccolo e pratico: quello che serve perché logo, video, presentazione, PDF e le
prossime pagine si somiglino. La tavola visiva è [`anteprima.png`](./anteprima.png)
(sorgente [`anteprima.html`](./anteprima.html)); i valori sono in
[`tokens.css`](./tokens.css) (variabili CSS) e [`tokens.json`](./tokens.json).

## Colori

Il **verde acqua** `#12A594` domina: il marchio e un'azione per schermata. Su fondo
scuro diventa **menta** `#5FE0CC`. Il **verde scuro** `#0B6F64` è il testo sul
verde chiaro `#E1F5F1` e lo sfondo dell'icona. Le scene e le slide di apertura e
chiusura sono su **notte** `#111413`, il resto su **sfondo** `#F4F7F6` con carte
bianche.

Gli **accenti** dicono che tipo di cosa è, non decorano: blu per documenti ed
ecografie (e i nostri messaggi in chat), viola per esercizi e marketing, ambra per
lista d'attesa, nutrizione e note interne, rosa per cardiologia e allergie, verde
per fatto e confermato. Ognuno ha la sua versione chiara per lo sfondo.

## Tipografia

**Inter** per web, app e video (la stessa del CRM); in PowerPoint e nel PDF
**Calibri** (Carlito dove Calibri non c'è, ha le stesse misure). Titoli in grassetto
con la spaziatura stretta (−0,035 em sui titoli grandi), testo a 16 px, etichette
in maiuscoletto a 13 px con la spaziatura larga.

## Forme e profondità

Raggi morbidi: 8 px per campi ed etichette, 12 per pulsanti e righe, 18–20 per
finestre e carte, pillole tonde per chip e stati. Ombre morbide e **tinte del verde
scuro**, mai nero puro; le carte hanno un bordo sottile `#E3E9E7`. In PDF le ombre
vanno stampate come immagini sfumate: Chromium rende male `box-shadow`.

## Icone

Lucide, tratto 2, angoli arrotondati; nel CRM le stesse di frappe-ui. Dentro un
cerchio o un quadrato arrotondato di colore chiaro, con l'icona nel colore pieno.

## Movimento

| Cosa | Curva | Durata |
|---|---|---|
| Qualcosa arriva (carte, righe, parole) | veloce e si posa, `cubic-bezier(.22,1,.36,1)` | 500 ms, 60 ms fra un elemento e l'altro |
| Cose piccole (spunte, badge) | con un leggero rimbalzo, `cubic-bezier(.34,1.56,.64,1)` | 250–500 ms |
| Camera e spostamenti | accelera e rallenta, `cubic-bezier(.65,0,.35,1)` | 800 ms |

La camera zooma sul prodotto, mai sui titoli. Niente oscillazioni continue sul
testo: tremola. Ogni riga resta ferma almeno 0,3 s per parola; dove parla
l'interfaccia, poco testo.

## Suono

Un campanello solo per gli eventi veri (confermato, inviato, firmato, riconosciuto);
niente tintinnii sugli elementi che compaiono. Le transizioni suonano solo quando
aprono spazio (i capitoli, i passaggi che attraversano lo schermo, l'ingresso nel
buio), e ognuna con un suono diverso.

## Linguaggio

Italiano semplice, frasi corte, verbi. Si dice cosa fa per il centro ("La fattura
nasce dalla visita"), non come è fatto. Niente prezzi nei materiali di
presentazione, niente superlativi, niente inglesismi inutili.
