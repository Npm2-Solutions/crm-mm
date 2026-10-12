// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// What the browser keeps of a session after it, and what takes it away.
import fs from 'node:fs'
import path from 'node:path'
import { COPIE_DI_FRAPPE_UI, togliLeCopie } from '@/utils/esci'

describe('togliLeCopie', () => {
  afterEach(() => {
    delete globalThis.indexedDB
  })

  it('deletes the database frappe-ui kept its copies in', () => {
    const tolti = []
    globalThis.indexedDB = { deleteDatabase: (nome) => tolti.push(nome) }
    togliLeCopie()
    expect(tolti).toEqual([COPIE_DI_FRAPPE_UI])
    // idb-keyval's own store, as the pinned version names it
    const idbKeyval = fs.readFileSync(
      path.resolve(
        import.meta.dirname,
        '../../node_modules/idb-keyval/dist/index.js',
      ),
      'utf8',
    )
    expect(idbKeyval).toContain(`createStore('${COPIE_DI_FRAPPE_UI}'`)
  })

  it('asks nothing of a browser without IndexedDB, or that refuses it', () => {
    expect(() => togliLeCopie()).not.toThrow()
    globalThis.indexedDB = {
      deleteDatabase: () => {
        throw new Error('SecurityError')
      },
    }
    expect(() => togliLeCopie()).not.toThrow()
  })
})
