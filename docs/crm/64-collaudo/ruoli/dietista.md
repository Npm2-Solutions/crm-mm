# Collaudo · Dietista

## A cosa serve

Questa è la giornata del dietista del Poliambulatorio San Luca: la visita pagata
online, la prima visita nutrizionale, il menu della settimana con gli alimenti della
libreria, la dieta a scambi, la lista della spesa, le abitudini, un programma a
tempo, il controllo in videochiamata, e l'apertura di una cartella fuori dalla sua
équipe. Ogni riga dice cosa fare e cosa deve succedere. Quando una riga non va come è
scritto, una segnalazione con il suo codice (per esempio DIE-05):
[segnalazioni.md](../segnalazioni.md).

## Prima di cominciare

- **Chi sei:** l'utente del ruolo `dietista`: livello Professionista, qualifica di
  dietista. Lavori a Milano il martedì e il giovedì, il venerdì pomeriggio e il
  sabato mattina, nello «Studio 3».
- **Dove:** `https://collaudo.dottorcloud.com/crm`, sul computer; *(telefono)* sul
  tuo telefono.
- **I pazienti:** i colleghi che fanno i pazienti. Misure, abitudini e diete
  inventate.

## La mattina

- [ ] **DIE-01 · Entra.** Dal computer; cambia la password (Impostazioni › Il tuo
  account › Profilo › «Cambia la password»).
  *Atteso:* l'agenda si apre sulla tua colonna.
  Note: ______________________________________________

- [ ] **DIE-02 · Il telefono *(telefono)*.** L'app sulla schermata Home e le notifiche
  accese (Impostazioni › Il tuo account › Notifiche).
  *Atteso:* la notifica di prova arriva.
  Note: ______________________________________________

- [ ] **DIE-03 · Una visita già pagata.** Apri l'appuntamento della «Visita
  nutrizionale» che il paziente ha prenotato e pagato per intero da `/prenota`
  ([paziente.md](./paziente.md)).
  *Atteso:* la fattura d'acconto (di prova) è già fatta ed è la fattura intera;
  «Fattura» sull'appuntamento dice «Questo appuntamento è già fatturato: fattura
  d'acconto …», e alla segreteria non resta niente da fatturare.
  Note: ______________________________________________

## La visita

- [ ] **DIE-04 · La prima visita.** Scheda Clinica › «Nuova visita» su «Prima visita
  nutrizionale»: misure, abitudini, obiettivi (inventati). «Firma».
  *Atteso:* il referto in PDF tra i Documenti; la visita non si modifica più.
  Note: ______________________________________________

- [ ] **DIE-05 · Il menu.** Scheda Piani › «Nuovo piano», un menu. Gli obiettivi del
  giorno (calorie e nutrienti), poi per la colazione «Scegli gli alimenti»: cerca per
  nome e per gruppo, scegline tre insieme.
  *Atteso:* ogni alimento con i grammi della sua porzione e le sue kcal; i totali del
  giorno accanto agli obiettivi, da dove viene l'energia, carboidrati e grassi
  confrontati con gli intervalli LARN.
  Note: ______________________________________________

- [ ] **DIE-06 · La settimana.** Completa il lunedì, poi «Copia in altri giorni…» fino
  a venerdì; cambia un alimento del mercoledì con un'alternativa dello stesso gruppo.
  *Atteso:* i giorni copiati sono uguali e si cambiano uno per uno; l'alternativa ha
  la stessa energia.
  Note: ______________________________________________

- [ ] **DIE-07 · Come si misura a casa.** Guarda come il menu dice i grammi di un
  cucchiaio d'olio o di un bicchiere di latte.
  *Atteso:* accanto ai grammi la misura di cucina («1 cucchiaio»), anche nell'area del
  paziente.
  Note: ______________________________________________

- [ ] **DIE-08 · Pubblicare.** «Pubblica».
  *Atteso:* il paziente vede il menu nell'area, giorno per giorno; il piano porta il
  segno dei dati sanitari.
  Note: ______________________________________________

- [ ] **DIE-09 · La lista della spesa.** Sul menu, «Lista della spesa» per la
  settimana.
  *Atteso:* i grammi sommati sul server per i giorni chiesti; la lista si copia per il
  paziente; nell'area il paziente la spunta, e le spunte restano sul suo telefono.
  Note: ______________________________________________

- [ ] **DIE-10 · La dieta a scambi.** A un secondo paziente, un piano a scambi.
  *Atteso:* i gruppi e le porzioni da scambiare; si pubblica allo stesso modo.
  Note: ______________________________________________

- [ ] **DIE-11 · Le abitudini.** Un piano di abitudini (bere due litri d'acqua,
  camminare): una voce ogni giorno.
  *Atteso:* il paziente spunta ogni voce con un tocco; tu vedi cosa ha fatto questa
  settimana.
  Note: ______________________________________________

- [ ] **DIE-12 · Il programma a tempo.** Un programma «Con il tempo» di tre tappe, una
  al mese, ognuna con il suo piano.
  *Atteso:* la prima tappa è aperta oggi; la seconda si apre da sola il giorno che le
  hai dato.
  Note: ______________________________________________

- [ ] **DIE-13 · Il modello.** «Salva come modello» il menu; per un altro paziente
  «Parti da un modello».
  *Atteso:* il menu nuovo ha gli stessi alimenti e obiettivi; cambiarlo non tocca il
  modello.
  Note: ______________________________________________

- [ ] **DIE-14 · Gli alimenti del centro.** Se il responsabile ti ha dato le librerie:
  Impostazioni › Pazienti › Librerie › Alimenti, spegni un alimento e aggiungi «Un
  alimento nuovo» del centro.
  *Atteso:* l'alimento spento non si offre più nei menu nuovi; quello nuovo sì; quelli
  della libreria di DottorCloud non si cambiano.
  Note: ______________________________________________

- [ ] **DIE-15 · Le ricette (se l'assistente è acceso).** Sul menu, chiedi
  all'assistente una ricetta con gli alimenti scelti.
  *Atteso:* una proposta da rileggere; resta solo se la tieni, come alimento della
  libreria del centro.
  Note: ______________________________________________

## Il pomeriggio

- [ ] **DIE-16 · Il controllo online.** All'ora del «Controllo nutrizionale online»,
  dal pannello dell'appuntamento «Avvia la visita online».
  *Atteso:* si apre la stanza Jitsi (su `meet.jit.si` entri con il tuo account
  Google, GitHub o Facebook); il paziente entra dalla sua area con «Entra nella
  visita», da 15 minuti prima; il link della stanza non è in nessuna email né SMS.
  Note: ______________________________________________

- [ ] **DIE-17 · Fuori dalla tua équipe.** Da Persone, una paziente del
  fisioterapista che non è tua: «Apri una cartella fuori dalla tua équipe», scrivi
  perché.
  *Atteso:* la cartella si apre per un giorno; il motivo resta nel registro degli
  accessi e il direttore sanitario lo legge
  ([medico-direttore-sanitario.md](./medico-direttore-sanitario.md), MED-19).
  Note: ______________________________________________

## La sera

- [ ] **DIE-18 · Gli esiti.** I tuoi appuntamenti ancora senza esito: «Presente» o
  «Assente».
  *Atteso:* puoi segnare i tuoi, non quelli dei colleghi.
  Note: ______________________________________________

- [ ] **DIE-19 · Sul telefono *(telefono)*.** Apri il menu di un paziente sul
  telefono e cambia un alimento.
  *Atteso:* ogni alimento è una riga con il suo segno, i grammi e le kcal; i totali
  del giorno si leggono senza girare il telefono.
  Note: ______________________________________________
