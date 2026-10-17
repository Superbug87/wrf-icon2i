# WRF sul Lazio

Previsione a 48 ore con **WRF** (modello fisico vero) su tre domini annidati centrati sul Lazio
(41,82 N, 12,72 E): **18 km → 6 km → 2 km**. Il dominio a 2 km (300 km di lato) copre tutta la regione. Parte dai dati aperti di **ECMWF**
(IFS 0,25°; GFS è l'alternativa) e gira ogni giorno sui server gratuiti di GitHub. Alla fine disegna le mappe
(30 tipi: temperatura a 2 m, 925 e 850 hPa, zero termico, umidità, vento medio, raffiche, pioggia 1/3/6/12/24 h,
neve 6/24 h, pressione, nuvolosità totale/bassa/media/alta, CAPE (parcella più instabile e strato mescolato), CIN, shear 0-1/0-3/0-6 km,
elicità 0-1/0-3 km, rischio fulmini, rischio supercelle, rischio tornado), una ogni 6 ore, più una immagine per ogni ora e variabile, e le pubblica nel ramo `risultati`.

Nasce dal progetto gemello **wrf-castelli** (stessa catena, tre domini a 9 → 3 → 1 km sui Castelli Romani): qui cambiano la
geometria dei domini, il passo di calcolo, le stazioni, il mare, le mappe e il radar; compilazione, scarico dei dati, ungrib,
metgrid, real, segmenti e pubblicazione sono gli stessi. Questo repository è **ancora tutto da provare su GitHub**: vedi
«Stato del collaudo».

## Avvertenze
- **Progetto personale e sperimentale, non un servizio ufficiale.** Le previsioni sono prodotte in automatico da un modello
  numerico, senza il controllo di un meteorologo, e possono essere sbagliate, anche di molto. Per pioggia e temporali
  posizione e orario possono sbagliare di chilometri e di ore.
- **Non sostituiscono i bollettini e le allerte ufficiali** (Protezione Civile, Aeronautica Militare, centri funzionali
  regionali). Non usarle per decisioni che riguardano la sicurezza di persone o cose: protezione civile, volo,
  navigazione, lavori o eventi a rischio.
- **Nessuna garanzia.** Sono fornite «così come sono», senza garanzie di esattezza, continuità o disponibilità: il servizio
  può ritardare, fermarsi o dare errori. L'autore non risponde di danni derivanti dall'uso.
- **Nessun legame con i fornitori dei dati.** Il progetto non è collegato a ECMWF, NOAA, NCAR/UCAR, Weather Underground né
  agli altri fornitori elencati sotto e non è da loro approvato o rivisto.

## Che cosa cambia rispetto ai Castelli Romani
| | Castelli Romani | Lazio |
|---|---|---|
| domini | 9 → 3 → 1 km (450, 162, 60 km di lato) | 18 → 6 → 2 km (936, 432, 300 km di lato) |
| passo di calcolo | 45 s (nidi: 15 s e 5 s) | 90 s (nidi: 30 s e 10 s) |
| convezione | esplicita da 3 km in giù | Kain-Fritsch a 18 e 6 km, esplicita a 2 km |
| mappe | 40 x 40 km, passo ~1 km | 256 x 256 km (40,67-42,97 N, 11,18-14,26 E), passo ~2 km |
| stazioni nel nudging | fino a 40 / 30 / 20 | **tutte** quelle trovate nell'area del dominio a 2 km (in una prova ne ha trovate circa 2100; quante restano dopo i controlli lo dice il log), nessun tetto |
| raggio del nudging | 100 / 50 / 25 km | 200 / 100 / 50 km |
| temperatura del mare (MUR) | 1 km, 39-44,5 N 9-16,5 E | un punto ogni 2 km, 35,5-48 N 4-21,5 E |
| radar | un pixel ogni punto della mappa | media dei pixel da 1 km attorno a ogni punto da 2 km |

**Perché 2 km e non 1 km su tutta la regione.** Il Lazio è circa 230 x 210 km: un dominio a 1 km che lo coprisse con i margini (circa 300 x 300 km)
avrebbe circa 90 000 colonne e il calcolo non starebbe nei tempi gratuiti di GitHub. A 2 km (151 x 151 colonne, passo di 10 s) il costo
(celle x passi) è circa 3 volte quello del vecchio assetto a 27/9/3 km: stima 1,5-2 ore per segmento di 16 ore, da confermare con il
primo run. Le celle a 2 km risolvono i temporali in modo esplicito (senza parametrizzazione), ma non le valli strette dell'Appennino. Per il dettaglio
sui Castelli resta il progetto gemello.

## Prima di cominciare
- Il repository deve essere **pubblico**: i server sono da 4 processori e i minuti sono illimitati.
  In un repository privato i server hanno 2 processori e 2000 minuti al mese: non bastano.
- Facoltativo ma consigliato: la chiave Wunderground, per far entrare le stazioni dentro WRF (vedi sotto).
  Su GitHub: *Settings → Secrets and variables → Actions → New repository secret*, nome `WU_API_KEY`.
- **La prima volta tutto parte da zero**: le cache di GitHub non si condividono tra repository, quindi WRF e WPS vanno
  ricompilati e i dati geografici rifatti anche qui.

## Come si avvia (anche da telefono)
1. App GitHub (o sito) → il repository → **Actions** → **Previsione WRF Lazio** → **Run workflow**.
2. Campi: `pilota` (`ecmwf` di default, oppure `gfs`), `ciclo` (vuoto = l'ultimo completo; per ECMWF solo le 00 e le 12 UTC),
   `ore` (default 48), `ore_segmento` (default 16), `stazioni` (nudging, sì di default), `mare` (temperatura del mare
   MUR, sì di default), `radar` (confronto con il radar e pioggia delle prossime 3 ore, sì di default).
3. **L'avvio automatico è attivo** (righe `schedule` in `.github/workflows/wrf.yml`, dopo la prima esecuzione completa
   riuscita del 16-17 ottobre 2026, circa 2 h 30): 09:10 UTC (ciclo ECMWF delle 00 UTC, pubblicato verso le 07:35) e
   20:20 UTC (ciclo delle 12 UTC, verso le 19:35). Per spegnerlo basta commentare di nuovo quelle righe. Gli orari sono
   sfalsati di mezz'ora rispetto ai Castelli: le due catene usano la stessa chiave Wunderground e così non chiamano insieme.

Tempi **stimati** (non ancora misurati qui; la compilazione e i dati statici sono quelli dei Castelli, il calcolo no):

| fase | quando | durata |
|---|---|---|
| compilazione di WRF e WPS | solo la prima volta | 40-90 min |
| dati statici (terreno, uso del suolo) | solo la prima volta | 30-60 min (il dominio esterno è 8 volte più esteso: forse di più) |
| scarico ECMWF, ungrib, metgrid, real | ogni giorno | 10-20 min |
| stazioni Wunderground (ricerca e lettura, in parallelo) | ogni giorno | circa 3 min (misurato: 30 s di ricerca e 100 s di lettura per ~2100 stazioni) |
| WRF, 3 segmenti da 16 h in fila | ogni giorno | stima 1,5-2 h ciascuno (da misurare con i 2 km) |
| mappe e pubblicazione | ogni giorno | 5-10 min |

GitHub ferma ogni job dopo 6 ore, per questo la previsione è divisa in segmenti che ripartono dal *restart*
del precedente. Se i segmenti vanno stretti, abbassa `ore_segmento` (massimo 4 segmenti) o `ore`.
Le uscite del dominio a 2 km (151 x 151 colonne) pesano circa il doppio di quelle del vecchio assetto a 3 km.

**La compilazione è a tappe** (`wrf/costruisci.sh prepara|wrf|wps|installa`, quattro passi del job `costruzione`):
- mentre WRF compila, il log scrive ogni 5 minuti a che punto è (oggetti compilati, ultimo file, carico, memoria);
- se in 30 minuti non cambia nulla (né file compilati né righe di log) un guardiano stampa quali processi sono rimasti
  appesi, salva la diagnosi (`diagnosi.txt`, tra gli allegati `log-compilazione`) e ferma il job invece di lasciarlo girare
  fino al limite;
- c'è un tempo massimo di 290 minuti per WRF: se scade, il sorgente parziale (con gli oggetti già compilati) va in cache
  e **rilanciando il flusso la compilazione riprende da lì**, senza ricominciare;
- la cache finale (`wrf-install`) si salva solo se tutte e quattro le tappe finiscono; quella parziale (`wrf-src`) si salva
  anche se si interrompe.

## Dove trovo i risultati
- Ramo **`risultati`** del repository: la cartella `ultimo/` e il suo `README.md` con tutte le immagini
  (si legge bene dall'app GitHub). In `archivio/` ci sono gli ultimi 28 cicli (14 giorni).
- Stesso ramo, cartella **`orarie/`**: una immagine per ogni ora e per ogni tipo di mappa (solo tipo, ora del run e ora
  della mappa, senza descrizioni), degli ultimi 14 cicli (una settimana: 30 variabili x 49 ore a 64 colori, circa 60-100 KB l'una, 60-80 MB a ciclo e circa 1 GB per i 14 cicli);
  `orarie/cicli.json` elenca i cicli presenti, `orarie/<ciclo>/indice.json` variabili e ore di ciascuno. Il ramo viene
  riscritto con un solo commit a ogni pubblicazione, così la storia non cresce.
- **Sul sito**: la pagina `sito/previsioni-wrf-lazio.html` (un solo file, senza dipendenze) sfoglia le immagini
  orarie: scelta del run (una settimana di previsioni), del tipo di mappa, cursore delle ore, scarico dell'immagine e della
  GIF dell'intero run, tasto play, frecce, scorrimento col dito, salto al giorno (identica a quella dei Castelli Romani).
  Va caricata sul sito (FTP) e legge le immagini direttamente da GitHub (`raw.githubusercontent.com`), che le tiene in
  cache circa 5 minuti: si aggiorna da sola quando esce un nuovo ciclo. Si può anche incorporare con un `<iframe>`.
  **Caricamento automatico (FTP)**: `.github/workflows/sito.yml` + `wrf/carica_sito.sh` caricano la pagina a ogni
  sua modifica. Servono quattro segreti del repository (Settings → Secrets and variables → Actions): `FTP_HOST`,
  `FTP_USER`, `FTP_PASSWORD`, `FTP_CARTELLA` (es. `5archi`). Senza segreti il flusso non fa nulla.
- In *Actions → l'esecuzione → Artifacts*: `mappe` (le immagini) e, se qualcosa va storto, i log.

## Cosa fa e cosa non fa
- WRF è alimentato da un solo modello globale per volta (ECMWF o GFS).
- **Stazioni Wunderground dentro WRF (nudging).** Con la chiave `WU_API_KEY`, prima del calcolo si cercano **tutte** le
  stazioni nell'area del dominio a 2 km (il Lazio più un margine attorno). Ogni ricerca ne dà al massimo 10, quindi l'area si
  divide in riquadri e ogni riquadro in cui le 10 stazioni più vicine non bastano a coprirlo si divide ancora, fino a riquadri
  di mezzo km nei centri abitati; le ricerche e le letture girano in parallelo (24 alla volta, al massimo 40 chiamate al
  secondo). Di ogni stazione si legge la posizione/quota attuale e lo storico delle ultime 24 ore. Poi si **scartano quelle
  con dati sballati**: mute da più di 3 ore, quota dichiarata incoerente con il terreno del modello (oltre 400/600/800 m nei tre
  domini), senza temperatura, con il sensore bloccato (temperatura identica per 3 ore) o con più della metà dei valori fuori
  dalle vicine. I valori si confrontano con quelli delle 12 stazioni più vicine, riportati alla stessa quota (6,5 K/km): fuori
  se si discostano dalla loro mediana più di 3 volte lo scarto tipico e più di una soglia minima (temperatura 3-8 K, umidità
  25-40 %, pressione 2-4 hPa, crescente con la distanza delle vicine); si tolgono anche i salti improvvisi nel tempo. La
  pressione sbagliata (di solito quella non riportata al mare) si toglie da sola, senza eliminare la stazione. Nel collaudo
  con dati veri (1781 stazioni, 9 ore di dati, terreno inventato) sono stati scartati circa il 2 % delle temperature, lo 0,6 % delle umidità e l'11 % delle pressioni.
  Il resto si media ogni 15 minuti. WRF, dall'inizio del ciclo fino all'ultima osservazione, spinge temperatura e umidità
  verso quei valori (raggio di influenza 200/100/50 km nei tre domini, tempo di rilassamento circa mezz'ora); poi prosegue
  libero dallo stato raggiunto. Il **vento delle stazioni non viene usato**: gli anemometri amatoriali sono quasi sempre
  riparati. Senza chiave o senza dati utili WRF gira senza nudging. In questo caso le mappe applicano la correzione
  dopo il calcolo (scala 5 km), sempre con tutte le stazioni del riquadro; con il nudging non si corregge una seconda volta.
  Limiti: i sensori amatoriali sono di qualità diversa (quelli al sole di giorno scaldano), nei centri abitati le stazioni
  sono centinaia e pesano molto sul risultato locale, e l'effetto sulle ore lontane dall'ultima osservazione è piccolo: il
  nudging migliora lo stato di partenza, non cancella gli errori del modello globale. I file delle osservazioni crescono
  (circa 75 MB in chiaro per ciclo, circa 7 MB compressi e cifrati tra un segmento e l'altro). Assimilare le stazioni con
  un'analisi vera (WRFDA) sarebbe un lavoro a parte.
  **Chiamate**: ogni ciclo ne usa circa 4000 (1150 per la ricerca, 2 per stazione per la lettura), due cicli al giorno circa
  8000, più il flusso dei Castelli con la stessa chiave. Wunderground dichiara per le chiavi personali 1500 chiamate al giorno
  e 30 al minuto; nelle prove (circa 5000 chiamate in una sera, fino a 80 al secondo) non ha mai rifiutato nulla. Se un giorno
  rifiutasse ("troppe richieste") più volte di fila, il programma smette di chiamare e usa le stazioni già lette, senza fallire.
  Si regola con `WU_CHIAMATE_AL_SECONDO` (default 40) e `WU_THREAD` (default 24).
- **Temperatura del mare.** ECMWF dà la temperatura del mare a 25 km. Per il mare si scarica l'analisi MUR SST di NASA JPL
  (0,01°, circa 1 km, qui diradata a un punto ogni 0,02°, con 1-2 giorni di ritardo, tenuta costante per le 48 ore) e WRF la usa sui punti d'acqua
  al posto di quella del modello globale. Il riquadro scaricato copre tutto il dominio a 18 km.
  Se il servizio non risponde, WRF gira lo stesso con la temperatura del mare del modello globale.
- **Radar (Protezione Civile).** Due immagini in più, `radar_1_verifica` e `radar_2_prossime_3_ore`, e un CSV nell'archivio.
  *Verifica*: per le ultime ore (fino a 6) la pioggia oraria misurata dal radar nazionale (prodotto SRI, mosaico a 1 km
  ogni 5 minuti, mediata sui 2 km di WRF) accanto a quella di WRF, con la media sull'area delle mappe (256 x 256 km), la quota di area bagnata
  e un indice di accordo di posizione (FSS, soglia 0,5 mm in un'ora, controllato su circa 10 km). *Prossime 3 ore*: il radar spostato lungo il movimento che
  ha adesso, WRF per le stesse ore, e un mix dei due in cui il peso del radar scende da 83% (prima ora) a 17% (terza).
  I pesi sono una scelta di buon senso, **non tarati**. Se il radar non risponde lo script esce e le mappe di WRF non cambiano.
  Cosa dicono i collaudi fatti nel progetto dei Castelli (radar vero, ultimi 4 giorni, 76 casi su riquadri di 300 km in tutta
  Italia, confronto con «la pioggia resta dov'è»): spostare la pioggia **non migliora in media** l'accordo di posizione
  (differenza tra −0,02 e +0,02, indistinguibile da zero). Se però il movimento stimato è rapido (oltre circa 24 km/h) si guadagna
  poco (circa +0,04 su una base di circa 0,25), mentre con movimenti lenti spostare peggiora (circa −0,03). Per questo sotto quella
  velocità la pioggia è lasciata ferma. Un singolo episodio di pioggia organizzata (12 ottobre sul Lazio) andava molto
  meglio (accordo a un'ora 0,68 contro 0,43), ma è un caso favorevole, non la regola. Il radar non prevede la nascita dei
  temporali: dopo 1-2 ore conta soprattutto WRF. Il radar stesso può sbagliare (echi dei monti, schermature, calibrazione).
  Il confronto con WRF vero non è stato ancora visto. Il CSV (`archivio/<ciclo>/radar_verifica.csv`) serve a vedere nel tempo
  se WRF migliora e a tarare i pesi.
- **Raffiche = stima**: massimo orario del vento a 10 m di WRF (`nwp_diagnostics`) e raffica «turbolenta» (vento medio + 7,71 u\* f,
  con f che cresce con l'instabilità, metodo del modello ECMWF, Bechtold e Bidlot 2009); la mappa mostra il più alto dei due.
  Non ancora tarata sulle raffiche misurate dalle stazioni: si regola con la variabile d'ambiente `WRF_FATTORE_TURBOLENZA` (1 = metodo originale).
- **CAPE e CIN = stima** calcolate colonna per colonna su tutti i livelli di WRF: parcella più instabile (MU, nei primi 300 hPa) e strato mescolato
  (ML, 100 hPa), con temperatura virtuale e livello di libera convezione. Controllate contro MetPy su profili simili a quelli di WRF
  (scarti attorno al 10% per ML, molto meno per MU): è un controllo del calcolo, non della previsione.
- **Zero termico, T a 925 e 850 hPa**: interpolati in ln p; sotto il suolo si estrapola con 6,5 K/km. **Nuvolosità**: da CLDFRA con
  sovrapposizione massima-casuale (bassa sigma > 0,8, media 0,45-0,8, alta < 0,45). **Neve fresca**: precipitazione solida di WRF con densità di
  Hedstrom e Pomeroy (1998), non accumulata sul suolo. **Shear e SRH**: vento a quote fisse sopra il suolo, moto della tempesta di Bunkers.
- **Rischio fulmini, supercelle e tornado sono INDICI, non probabilità.** Fulmini: LPI di WRF (`lightning_option = 3`) e corrente ascendente × graupel;
  supercelle: tipo SCP (CAPE, CIN, SRH 0-3 km, shear 0-6 km); tornado: tipo STP (CAPE e CIN del livello mescolato, base delle nubi, SRH 0-1 km, shear 0-6 km).
  Nascono su dati degli Stati Uniti e **non sono tarati sull'Italia**: dicono dove le condizioni sono favorevoli, non quanto è probabile l'evento.
  I tornado sono eventi di scala molto più piccola dei 2 km: l'indice segnala un ambiente, non prevede un tornado. Ogni mappa lo dichiara in basso.
- ECMWF (come GFS) ha punti ogni 25 km: i 2 km vengono da WRF e dall'orografia, non dal dato di partenza.
- I dati ECMWF sono quelli *open data* (licenza CC-BY 4.0): per ogni ora si scaricano solo i campi che servono
  (circa 40 MB invece di 140), si ritagliano su Mediterraneo e Europa (30-54 N, 0-32 E, più del dominio a 18 km) e si riscrivono con compressione semplice perché
  `ungrib` non legge la compressione CCSDS di ECMWF. Gli strati di suolo, numerati da 1 a 4, diventano
  profondità in cm (0-7, 7-28, 28-100, 100-289) e l'orografia dell'ora 0 è copiata in tutte le ore.
- Le mappe mostrano una stella per Velletri (il valore scritto in basso a destra di ogni riquadro) e le città principali.
- **Il vento è disegnato come linee di flusso** (come le carte di Meteociel): linee continue sottili con tante freccette
  piene lungo la linea (una ogni ~18 km) che danno il verso, oltre 100 linee e più di 600 freccette nelle immagini orarie (prima
  erano 100 frecce corte). Le tessere da 6 ore sono meno fitte. Il colore sotto resta la velocità del vento. Si regola con
  `densita` in `disegna_flusso()` (`previsioni_lazio.py`).
- Il bordo del dominio a 2 km è a 25 km o più dalle mappe, ma le celle vicino al bordo del nido sono comunque influenzate
  dal dominio a 6 km: non fidarsi troppo dei dettagli ai margini della mappa.
- Non sostituisce le previsioni ufficiali.

## Fonti dei dati e licenze
| cosa | fonte | condizioni |
|---|---|---|
| Dati di partenza e al contorno (default) | [ECMWF IFS open data](https://www.ecmwf.int/en/forecasts/datasets/open-data), 0,25°, [doi:10.21957/open-data](https://doi.org/10.21957/open-data) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) e condizioni d'uso ECMWF. **Dati modificati**: ritagliati, ricodificati e usati come condizioni iniziali e al contorno di WRF. ECMWF non garantisce i dati e non risponde di errori o omissioni |
| Dati di partenza alternativi | [GFS di NOAA/NCEP](https://www.nco.ncep.noaa.gov/pmb/products/gfs/) | dati pubblici del governo statunitense; NOAA non approva questo lavoro |
| Temperatura del mare (facoltativa) | [MUR SST](https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1) di NASA JPL (0,01°, circa 1 km, diradata a 0,02°), via [NOAA CoastWatch ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/), citazione: JPL MUR MEaSUREs Project, 2015, [doi:10.5067/GHGMR-4FJ04](https://doi.org/10.5067/GHGMR-4FJ04) | dati NASA ad accesso libero, si chiede di citare la fonte |
| Radar (facoltativo) | [Radar-DPC](https://radar.protezionecivile.it), Dipartimento della Protezione Civile, mosaico nazionale SRI (intensità di pioggia) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/): va citata la fonte e le immagini ricavate (`radar_*`) hanno la stessa licenza. Dati usati solo per le due immagini radar, non ripubblicati in forma grezza; il CSV contiene solo medie sull'area |
| Modello | [WRF e WPS](https://www2.mmm.ucar.edu/wrf/users/public.html) di NCAR/UCAR | software pubblico, non incluso qui: lo compila il flusso di lavoro dai sorgenti ufficiali |
| Terreno e uso del suolo | dati geografici [WPS_GEOG](https://www2.mmm.ucar.edu/wrf/users/download/get_sources_wps_geog.html) di NCAR/UCAR (tra cui GMTED2010 di USGS/NGA e MODIS) | scaricati durante il calcolo, non inclusi qui; vale la licenza di ciascun dato |
| Confini regionali e provinciali | confini amministrativi ISTAT, elaborati da [Openpolis](https://github.com/openpolis/geojson-italy) ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)) | semplificati (100 m) e ritagliati sull'area delle mappe in `dati/confini_lazio.json`; la fonte è citata a piè di mappa |
| Laghi | contorni di [OpenStreetMap](https://www.openstreetmap.org/copyright) (© OpenStreetMap contributors, [ODbL](https://opendatacommons.org/licenses/odbl/)) | specchi d'acqua di almeno 1 km², semplificati (50 m), in `dati/laghi_lazio.json`; la fonte è citata a piè di mappa |
| Stazioni meteo | rete di stazioni amatoriali di [Weather Underground](https://www.wunderground.com/) (The Weather Company), tramite la chiave personale del proprietario | restano soggette ai termini d'uso di Weather Underground, da rispettare (la chiave è personale). I dati **non vengono ripubblicati**: si scaricano durante il calcolo, entrano in WRF e non finiscono nei risultati; i file temporanei che passano da un segmento all'altro sono cifrati; i log non riportano codici o posizioni delle stazioni; le mappe mostrano solo l'uscita del modello |
| Solo per `previsioni_lazio.py` usato da solo | [Open-Meteo](https://open-meteo.com/) ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); l'API gratuita è per uso non commerciale) e quote dal modello digitale del terreno Copernicus DEM («contiene dati Copernicus modificati») | non usati dalla catena WRF |

Librerie principali: ecCodes (Apache 2.0), JasPer, NumPy, SciPy, Matplotlib, netCDF4, requests, pyproj, OpenCV, tifffile: ciascuna con la sua licenza.
I nomi delle città e le posizioni sulle mappe sono scritti a mano nello script, non vengono da OpenStreetMap o altri archivi.
Le condizioni dei fornitori possono cambiare: prima di usare il progetto in modo diverso da quello personale
(per esempio per un servizio pubblico o commerciale) vanno ricontrollate.

## Stato del collaudo
**Nessuna esecuzione di WRF su GitHub è ancora stata fatta in questo repository.** Il codice è quello del progetto dei Castelli Romani
(dove compilazione, geogrid, segmenti e pubblicazione sono stati provati il 16 ottobre 2026, con le correzioni già incluse qui)
adattato al Lazio. Un primo run a 27/9/3 km è finito il 17 ottobre 2026; l'assetto a 18/6/2 km con le 30 mappe non è ancora stato eseguito.

Provato qui (in un ambiente senza compilatore Fortran): geometria dei tre domini (annidamento centrato, margini, mappe e
tutta la regione dentro il dominio a 2 km), namelist (letti da f90nml: passo di 90 s che divide segmenti, bordi e uscite
orarie), grandezze derivate (`wrf/diagnostiche.py`) su casi con risposta nota (atmosfera standard, vento che gira con la quota, neve, raffica), file delle stazioni (inventate) riletti con le istruzioni di lettura di WRF, file `SST` riletto con `rd_intermediate` di WPS,
mappe e immagini orarie a partire da file `wrfout` inventati con la struttura di WRF (griglia 151 x 151 a 2 km, 30 variabili),
mappe con dati inventati di `previsioni_lazio.py`, radar vero (scarico, media sui 2 km e le due immagini; il confronto con una pioggia vera
non è stato visto), pubblicazione nel ramo `risultati` su un repository finto, sintassi del flusso (actionlint in CI), degli script (shellcheck) e della pagina del sito.
Queste prove girano da sole a ogni modifica del codice: `wrf/prove.sh`, lanciato dal flusso **Prova automatica**
(`.github/workflows/prova.yml`, pochi minuti, non tocca le cache di WRF). Si può lanciare anche a mano: `bash wrf/prove.sh`
(con `PROVA_RADAR=1` prova anche il radar vero).

**Non provato in questo repository:** compilazione di WRF e WPS, download dei dati geografici NCAR, geogrid sul nuovo dominio
(936 km a 18 km), metgrid con il riquadro MUR esteso, real.exe e wrf.exe a 90 s
(stabilità numerica e tempi di calcolo da misurare), accettazione da parte di WRF di `nwp_diagnostics` e `lightning_option = 3`, nudging con oltre 1600 stazioni e raggi 200/100/50 km (file delle osservazioni grandi), uscite grandi
per segmento, pagina del sito con dati veri. Le scelte fisiche (Kain-Fritsch a 6 km, radiazione ogni 18/6/3 minuti, nessun
`slope_rad`) sono ragionevoli ma non tarate. Il primo avvio potrebbe richiedere qualche correzione: i log escono come artifact.

## File
- `.github/workflows/wrf.yml` — il flusso (automatico alle 09:10 e 20:20 UTC, o a mano)
- `wrf/dominio.py` — geometria dei tre domini · `wrf/config.py` — namelist di WPS e WRF
- `wrf/dipendenze.sh`, `costruisci.sh` (a tappe, con avanzamento e guardiano), `statico.sh`, `esegui.sh`, `pubblica.sh`
- `wrf/scarica_ecmwf.py` + `wrf/Vtable.ECMWF_OD` — dati ECMWF · `wrf/scarica_gfs.py` — alternativa GFS
- `wrf/diagnostiche.py` — CAPE/CIN, shear, SRH, nuvole, zero termico, indici di rischio, raffica e neve, colonna per colonna · `wrf/postprocess.py` — da `wrfout` alle mappe · `wrf/orarie.py` — una immagine per ora e variabile + `indice.json`
- `sito/previsioni-wrf-lazio.html` — pagina per sfogliare le immagini orarie (da caricare sul sito)
- `wrf/stazioni_wrf.py` — stazioni Wunderground nel formato di WRF per il nudging
- `wrf/scarica_sst.py` — temperatura del mare MUR nel formato intermedio di WPS (campo `SST`)
- `wrf/radar.py` — scarico del radar Radar-DPC, posizione sulla mappa, movimento · `wrf/pioggia_radar.py` — verifica e
  pioggia delle prossime 3 ore
- `wrf/prova_sintetica.py` — file `wrfout` (e `geo_em`) inventati per collaudare senza WRF · `wrf/prove.sh` — tutte le prove
  · `wrf/leggi_obs.f90` — rilegge i file delle stazioni con i formati di WRF · `wrf/prova_costruzione.sh` — prova
  avanzamento, tempo massimo e guardiano della compilazione con comandi inventati
- `.github/workflows/prova.yml` — prova automatica a ogni modifica · `.github/workflows/sito.yml` — carica la pagina sul sito
- `previsioni_lazio.py` — mappe e correzione con le stazioni (usato da `postprocess.py`)
- `dati/confini_lazio.json` — confine del Lazio e confini provinciali disegnati sulle mappe (linea spessa il Lazio, più
  sottili le province) · `wrf/prepara_confini.py` — lo rifà dai confini ISTAT di Openpolis (serve solo se cambiano)
- `dati/laghi_lazio.json` — contorni reali dei laghi (25, da 1 km² in su, isole comprese) · `wrf/prepara_laghi.py` — lo rifà
  da OpenStreetMap tramite Overpass
