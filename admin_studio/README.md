# Peak Season Admin Studio

Una dashboard nel browser per modificare testi, immagini e icone dell'app e per compilarla, senza scrivere codice e senza usare Claude.

## Avvio

- **Windows:** doppio clic su `Avvia_Admin_Studio.bat`.
- **Mac/Linux:** `./Avvia_Admin_Studio.sh`.

Si apre il browser su http://localhost:8765. Se quella porta è occupata (per esempio dall'anteprima web dell'app), lo studio usa la porta libera successiva e scrive l'indirizzo nella finestra nera. Per chiudere lo studio, chiudi la finestra nera.

## Requisiti minimi

- **Python 3.10 o successivo**, nel PATH come `python` o `py`.
- **Moduli Python**, da installare una volta con:
  ```
  python -m pip install -r admin_studio/requirements.txt
  ```
  I moduli sono Pillow, jsonschema e requests. Il server web usa solo la libreria standard: Flask non serve.
- **Per la compilazione dell'APK:**
  - Flutter. Lo studio lo cerca nella variabile `FLUTTER`, poi nel PATH, poi in `C:\src\flutter\bin\flutter.bat`.
  - Android SDK, con le licenze accettate una volta con `flutter doctor --android-licenses`.
- **Per le schede Icone e Immagini:** una connessione internet. Serve per le icone Material e per scaricare le foto.

## Schede

| Scheda | Cosa modifica | File |
|---|---|---|
| Testi App | i testi dell'interfaccia, in italiano e inglese; le chiavi non si possono cambiare | `data/ui_copy.json` |
| Corpus Condiviso | i testi comuni a più prodotti; una modifica vale per tutti i prodotti collegati | `data/database.json` |
| Descrizioni Prodotti | i testi di ogni prodotto: testo specifico oppure voce del corpus con un'eventuale aggiunta | `data/database.json` |
| Immagini | la foto principale (stella), il tipo di vista, la ricerca di nuove foto e il download da URL | `assets/images/`, `_metadata.json`, `_primary_manual.json`, database |
| Icone | l'icona di ogni stato, categoria, zona ed elemento dell'interfaccia | `data/ui_config.json` (e il database per le voci `database`) |
| Loghi | il logo di ogni fonte (caricato dal tuo computer), editore e titolo mostrati nei riquadri delle fonti, testo da cercare per trovare il logo; in alto l'elenco dei loghi che mancano, da copiare | `app/assets/sources/`, `fonti_locali/loghi_fonti/`, `scripts/config/source_display.json`, database |
| Link | tutti i link: generali (le fonti) e di ogni prodotto, che puoi modificare, aggiungere o eliminare | `scripts/config/link_overrides.json`, database |

**Salva Modifiche** salva i cambiamenti della scheda aperta e fa tre cose:
1. prima di scrivere, mette una copia di sicurezza in `data/_snapshots/_studio_backup_*`;
2. controlla il database con `scripts/validate_db.py`;
3. aggiorna i file dell'app in `app/assets` con `scripts/build_app_assets.py`.

Se il controllo trova errori, i file tornano com'erano.

I testi si possono anche esportare in CSV e reimportare (separatore `;`, si apre con Excel).

## Scaricare una foto

1. Nella scheda Immagini scegli il prodotto.
2. Usa i link rapidi (Wikimedia Commons per nome scientifico e inglese, USDA ARS) per trovare una foto.
3. Incolla l'indirizzo della pagina o della foto e premi **Scarica e Aggiungi alla Galleria**.

Autore, licenza e pagina sorgente si compilano da soli in due casi:
- **Wikimedia Commons:** li prende dall'API di Commons.
- **USDA ARS:** le foto sono di pubblico dominio; l'autore viene dalla didascalia "Photo by".

Per le altre fonti scrivi autore e licenza nel modulo: senza questi dati la foto non entra nella galleria. La foto viene salvata come `<id>_NN.jpg` (al massimo 2400 px) e convertita in WebP per l'app.

## Loghi delle fonti

1. In alto nella scheda Loghi c'è l'elenco dei loghi che mancano: premi **Copia Elenco** e cerca le immagini riga per riga. Ogni fonte ha anche il pulsante **Cerca Immagini**.
2. Salva l'immagine sul computer, meglio PNG grande e con sfondo trasparente.
3. Premi **Carica Logo** sulla fonte giusta.

Lo studio toglie lo sfondo chiaro uniforme e porta il logo a 128 px. Se il logo è scuro, lo segna perché nel tema scuro dell'app venga schiarito. L'originale resta in `fonti_locali/loghi_fonti/`.

Le modifiche ai link dei prodotti restano anche quando i link vengono rigenerati dagli script.

## Build & Deploy

Il pannello a destra mostra se database, testi, icone, foto e APK sono allineati con l'app.

- **Sincronizza App** aggiorna i file dell'app.
- **Compila APK Android** sincronizza i file, lancia `flutter build apk --release` con il log dal vivo e alla fine apre `build/app/outputs/flutter-apk/`.

Per vedere le modifiche nell'app aperta con `flutter run`, premi **R** maiuscola nel terminale di Flutter (Hot Restart). La `r` minuscola non basta, perché i file JSON si leggono solo all'avvio.

## File della cartella

- `studio.py`: server e API. Accetta richieste solo da questo computer (127.0.0.1) e può eseguire solo i comandi previsti.
- `images.py`: galleria e download.
- `sources.py`: loghi, editori e titoli delle fonti; link generali e per prodotto.
- `icons.py`: mappa delle icone.
- `static/`: la pagina (`index.html`, `studio.css`, `core.js`, `copy.js`, `images.js`, `icons.js`, `sources.js`, `build.js`).
- `requirements.txt`, `Avvia_Admin_Studio.bat`, `Avvia_Admin_Studio.sh`.
