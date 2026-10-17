# WRF con ICON-2I (Castelli Romani e Lazio)

Previsioni a 48 ore con **WRF** (modello fisico vero) che partono da **ICON-2I** (2,2 km, analisi con dati italiani e radar,
Agenzia ItaliaMeteo / MeteoHub) invece che da ECMWF. Due zone, ognuna con i propri domini annidati:

| zona | domini | cartella del codice |
|---|---|---|
| Castelli Romani | 9 → 3 → 1 km | `areas/castelli/` |
| Lazio | 18 → 6 → 2 km | `areas/lazio/` |

Sono la copia dei progetti **wrf-castelli** e **wrf-lazio** (che continuano a girare con ECMWF): stessa catena e stesse mappe (30 tipi),
cambia solo il dato di partenza. Così per ogni zona si hanno due previsioni con modelli diversi da confrontare.

**Non sostituisce le previsioni ufficiali.** Esperimento personale, può sbagliare. Gli indici di rischio (fulmini, supercelle, tornado)
non sono probabilità e non sono tarati sull'Italia.

## Come funziona
- Due flussi, `castelli.yml` e `lazio.yml` (automatici dopo i cicli 00 e 12 UTC di ICON-2I, o a mano). Ogni flusso copia la cartella della
  propria zona (`areas/<zona>/`) nella radice e poi esegue la stessa catena dei progetti gemelli: compilazione di WRF/WPS (una volta, in cache,
  condivisa dalle due zone), geogrid, scarico dei dati, ungrib, metgrid, real, WRF a segmenti da 16 ore, mappe, pubblicazione.
- **Dati**: `wrf/scarica_icon2i.py` entra in MeteoHub con l'account (segreti `MH_EMAIL`, `MH_PASSWORD`), scarica per ogni istante (ogni 6 ore) i campi sui
  65 livelli del modello (T, umidità, vento, pressione) e di superficie e suolo, li ritaglia (36,6-47,0 N, 6,0-19,6 E), porta i livelli del modello a 39 livelli
  di pressione e riscrive tutto in GRIB2 con gli stessi codici dei file ECMWF: così si riusa la stessa Vtable, ungrib, metgrid e real. Un solo scarico per ciclo
  (una cache lo passa dalla prima zona alla seconda). MeteoHub limita le richieste all'ora: lo script ne usa circa 11 per ciclo.
- **Suolo**: la temperatura si interpola in profondità; l'umidità, che ICON-2I dà per strati in kg m-2, si converte in frazione di volume e si media sugli
  strati di Noah. Sono stime: il modello di suolo di ICON (TERRA) non è quello di WRF.
- **Risultati**: ramo `risultati`, una cartella per zona (`castelli/` e `lazio/`, con `ultimo/`, `archivio/`, `orarie/`).
  Le pagine per sfogliare le immagini sono `areas/*/sito/previsioni-wrf-icon2i-*.html`.

## Segreti del repository (Settings → Secrets and variables → Actions)
- `MH_EMAIL`, `MH_PASSWORD`: account MeteoHub (obbligatori).
- `WU_API_KEY`: chiave Weather Underground, per il nudging sulle stazioni (facoltativa: senza, WRF gira libero).

## Stato
Prima versione: il convertitore ICON-2I → GRIB2 è provato fino alla lettura dei file con ecCodes; **WRF non ha ancora girato con questi dati**. Il primo avvio
compila WRF e WPS da zero (ore) e può richiedere correzioni. Il primo flusso da lanciare è quello dei Castelli (compila e mette in cache); il Lazio dopo.
Il codice delle due zone viene dai repository gemelli e non è sincronizzato in automatico.

## Dati e licenze
ICON-2I: Agenzia ItaliaMeteo, tramite [MeteoHub](https://meteohub.agenziaitaliameteo.it/) (le condizioni d'uso sono quelle della pagina «Attribuzioni e licenze» di MeteoHub:
da verificare prima di ripubblicare i dati). Le mappe sono elaborazioni di WRF (NCAR) su quei dati. Temperatura del mare: MUR SST (NASA JPL). Radar: Radar-DPC, Dipartimento della
Protezione Civile (CC BY-SA 4.0). Stazioni: Weather Underground, usate solo dentro il modello. Altre fonti come nei progetti gemelli.
