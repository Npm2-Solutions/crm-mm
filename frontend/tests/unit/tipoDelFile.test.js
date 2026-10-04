// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// An attachment's kind from its name, without the media types' database.
import { tipoDelFile } from '@/utils/tipoDelFile'

describe('what a file is, from its name', () => {
  it('knows pictures, whatever the case of the extension', () => {
    for (const nome of [
      'foto.png',
      'FOTO.JPG',
      'scan.jpeg',
      'x.heic',
      'a.webp',
    ])
      expect(tipoDelFile(nome), nome).toBe('immagine')
  })

  it('knows a PDF and plain text', () => {
    expect(tipoDelFile('referto.PDF')).toBe('pdf')
    expect(tipoDelFile('note.txt')).toBe('testo')
    expect(tipoDelFile('server.log')).toBe('testo')
  })

  it('calls every spreadsheet one, the old Excel ones too', () => {
    for (const nome of [
      'conti.xlsx',
      'conti.xls',
      'macro.xlsm',
      'a.ods',
      'export.csv',
    ])
      expect(tipoDelFile(nome), nome).toBe('foglio')
  })

  it('says nothing of the rest, of a name without an extension or of none', () => {
    expect(tipoDelFile('lettera.docx')).toBe('')
    expect(tipoDelFile('archivio.tar.gz')).toBe('')
    expect(tipoDelFile('referto')).toBe('')
    expect(tipoDelFile('')).toBe('')
    expect(tipoDelFile(null)).toBe('')
    expect(tipoDelFile(undefined)).toBe('')
  })
})
