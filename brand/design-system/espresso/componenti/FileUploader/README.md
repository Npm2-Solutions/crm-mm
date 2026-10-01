# FileUploader

Il caricamento di documenti: referti, consensi, immagini.

## In frappe-ui
`<FileUploader :fileTypes :validateFile @success>` con uno slot per l'area di rilascio; avanzamento con `Progress`.

## Personalizzazione DottorCloud
- L'area di rilascio ha la coda della nuvola e un segno a nuvola; quando ci passa sopra un file diventa `brand-subtle` e il segno mostra la **croce**.
- File caricati come righe con il Tag del tipo (PDF `blue`).
