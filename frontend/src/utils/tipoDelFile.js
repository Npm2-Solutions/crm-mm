// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// What a file is, from its name: an attachment's icon, and whether it can be
// looked at without leaving DottorCloud. Looked up in the media types' database
// (`mime`, 48 KB) that came with every person's page; and an .xls, an .xlsm or
// a .csv took the plain file's icon, the database not calling them spreadsheets.

const TIPI = {
  immagine: [
    'png',
    'jpg',
    'jpeg',
    'jpe',
    'jfif',
    'gif',
    'webp',
    'svg',
    'bmp',
    'heic',
    'heif',
    'avif',
    'tif',
    'tiff',
    'ico',
    'apng',
    'jxl',
  ],
  pdf: ['pdf'],
  foglio: ['xlsx', 'xls', 'xlsm', 'ods', 'csv', 'numbers'],
  testo: ['txt', 'text', 'log', 'ini', 'conf', 'def', 'list', 'in'],
}

const PER_ESTENSIONE = Object.fromEntries(
  Object.entries(TIPI).flatMap(([tipo, estensioni]) =>
    estensioni.map((estensione) => [estensione, tipo]),
  ),
)

/** 'immagine', 'pdf', 'foglio', 'testo', or '' for anything else. */
export function tipoDelFile(nome) {
  const estensione = /\.([a-z0-9]+)$/i.exec(String(nome || '').trim())?.[1]
  return (estensione && PER_ESTENSIONE[estensione.toLowerCase()]) || ''
}
