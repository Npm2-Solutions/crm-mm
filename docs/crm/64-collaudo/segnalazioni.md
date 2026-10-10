# 64 · Le segnalazioni

## A cosa serve

Un problema trovato nel collaudo vale solo se chi lo corregge lo può rifare. Questa
pagina dice cosa scrivere quando qualcosa non va come dice la lista del proprio
ruolo, quanto è grave, dove si raccoglie e che cosa succede dopo. Vale per i tre
livelli: la simulazione, il server di collaudo, il centro pilota.

## Cosa scrivere

| Campo | Cosa | Esempio |
|---|---|---|
| **Chi** | il ruolo che facevi, e il tuo nome | Segreteria, Silvia |
| **Livello** | 1 simulazione, 2 server di collaudo, 3 centro pilota | 2 |
| **Passo** | il codice della riga della lista | SEG-19 |
| **Dispositivo** | computer, telefono o tablet; il sistema e la versione; il browser; l'app sulla schermata Home o il browser; il testo grande, il tema scuro, il telefono girato | Samsung A54, Android 15, app installata, testo grande |
| **Quando** | il giorno e l'ora **al minuto**: servono per trovare il registro del server | 14/10/2026 10:42 |
| **Dove** | l'indirizzo della pagina (la barra del browser), o il nome della schermata | `/crm/accoglienza` |
| **Cosa ho fatto** | i passi, uno per riga, dall'inizio | 1. Accoglienza 2. «Emetti la fattura» 3. … |
| **Cosa mi aspettavo** | quello che dice la riga *Atteso*, o quello che ti sembrava ovvio | la fattura di prova con la fascia |
| **Cosa è successo** | le parole esatte di un messaggio, copiate, non riassunte | «Qualcosa è andato storto» |
| **Si ripete?** | sempre, a volte, una volta | sempre |
| **Schermata o video** | la schermata intera, o un video breve dello schermo | |

**Nel centro pilota:** mai il nome di un paziente, un suo dato sanitario o una
schermata con i suoi dati in una segnalazione su GitHub. Una persona si indica con il
codice della sua scheda (l'ultima parte dell'indirizzo, `/crm/persone/<codice>`);
una schermata si copre prima di allegarla, o si manda a NPM2 per la strada concordata
con il centro, mai per chat o email personale.

## La gravità

| Gravità | Quando | Cosa succede |
|---|---|---|
| **Bloccante** | ferma il lavoro e non c'è un'altra strada; o fa un danno: un messaggio alla persona sbagliata, dati sanitari letti da chi non deve, soldi presi o restituiti male, una fattura sbagliata che partirebbe, dati persi | si guarda subito; ferma il livello finché non è corretta. Nel pilota: si corregge in giornata, o si valuta il ritorno indietro |
| **Grave** | una cosa non funziona ma c'è un'altra strada; o fa credere una cosa sbagliata (un esito, un importo, uno stato) | si corregge prima di passare al livello dopo |
| **Minore** | funziona ma è scomoda, lenta, confusa; parole sbagliate o in inglese; sul telefono esce dallo schermo o si tocca a fatica | si decide: si corregge prima del pilota, o si accetta e si dice al centro |
| **Estetico** | l'aspetto, un refuso, un allineamento | si corregge quando si passa di lì |
| **Idea** | non è un errore: una cosa che servirebbe | va tra le proposte, non blocca niente |

Tutto quello che riguarda **chi vede cosa** (la cartella, i dati sanitari, le
conversazioni, i dati di un'altra persona) è almeno **Grave**, anche se sembra
piccolo. Nel dubbio tra due gravità, si sceglie la più alta: si abbassa dopo. Sono le stesse
gravità che usa la simulazione del livello 1 (bloccante, grave, minore, estetico).

## Dove si raccolgono

1. **Su GitHub**, nel repository di DottorCloud: New issue › «Segnalazione di
   collaudo». Il modello ha già i campi e l'etichetta `collaudo`
   (`.github/ISSUE_TEMPLATE/collaudo.md`). Il coordinatore crea l'etichetta una volta,
   se non c'è.
2. **Chi non ha GitHub** scrive sulla tabella qui sotto (stampata, o un foglio
   condiviso con la squadra), e il coordinatore apre le segnalazioni a fine giornata.
3. **Una segnalazione per problema.** Due problemi nella stessa schermata sono due
   segnalazioni; lo stesso problema trovato da due persone è uno solo, con un
   commento in più.

### La tabella

| N. | Data e ora | Chi (ruolo) | Dispositivo | Livello | Passo | Cosa è successo | Gravità | Issue | Stato |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |

Stato: aperta, in correzione, da riprovare, chiusa, accettata così.

## Che cosa succede dopo

1. **Ogni giorno**, ai dieci minuti della squadra (o del centro, nel pilota), il
   coordinatore legge le segnalazioni nuove e conferma la gravità.
2. Chi corregge scrive nella segnalazione il ramo o il commit, e la mette «da
   riprovare».
3. **Chi l'ha trovata la riprova** sul server di collaudo, con la stessa riga della
   lista, e la chiude, o la riapre con quello che vede adesso.
4. Una segnalazione «accettata così» dice perché, e chi l'ha deciso.
5. Alla riunione di fine livello si leggono tutte quelle ancora aperte: i criteri
   d'uscita ([README](./README.md)) dicono quante ne possono restare.
