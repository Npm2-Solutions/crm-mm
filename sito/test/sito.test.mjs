// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The site, built in a temporary folder and checked: every link and image
// leads somewhere, every page has its title and one <h1>, no price and no
// framework's name slip in; then the demo form's PHP, run with `php -S`, on
// the cases that matter. Run with: node --test sito/test/

import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { after, before, describe, test } from 'node:test'
import { fileURLToPath } from 'node:url'

const SITE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const OUT = fs.mkdtempSync(path.join(os.tmpdir(), 'sito-'))

const built = spawnSync(process.execPath, [path.join(SITE, 'build.mjs')], {
  env: {
    ...process.env,
    SITO_DIST: OUT,
    SITO_URL: 'https://dottorcloud.com',
    SITO_ANTEPRIMA: '',
  },
  encoding: 'utf8',
})

function pages(dir = OUT) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(dir, entry.name)
    if (entry.isDirectory()) return pages(file)
    return entry.name.endsWith('.html') ? [file] : []
  })
}

const text = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/g, ' ')
    .replace(/<style[\s\S]*?<\/style>/g, ' ')
    .replace(/<[^>]+>/g, ' ')

/** Where an address of the site leads, on disk. */
function target(href) {
  const clean = decodeURI(href.split('#')[0].split('?')[0])
  if (clean.endsWith('/')) return path.join(OUT, clean, 'index.html')
  return path.join(OUT, clean)
}

after(() => fs.rmSync(OUT, { recursive: true, force: true }))

describe('the build', () => {
  test('runs', () => {
    assert.equal(built.status, 0, built.stderr)
  })

  test('writes every page, the 404 and the files the server needs', () => {
    for (const page of [
      'index.html',
      'funzioni/index.html',
      'per-chi/index.html',
      'dati-e-privacy/index.html',
      'demo/index.html',
      'demo/grazie/index.html',
      'demo/errore/index.html',
      'privacy/index.html',
      'cookie/index.html',
      '404.html',
      'robots.txt',
      'sitemap.xml',
      'favicon.ico',
      'favicon.svg',
      'apple-touch-icon.png',
      'font/inter.woff2',
      'video/dottorcloud.mp4',
      'api/richiesta-demo.php',
      '.sito-dottorcloud',
    ]) {
      assert.ok(fs.existsSync(path.join(OUT, page)), `${page} is missing`)
    }
  })

  test('the sitemap lists the pages to index, and only those', () => {
    const sitemap = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8')
    assert.match(sitemap, /<loc>https:\/\/dottorcloud\.com\/<\/loc>/)
    assert.match(sitemap, /<loc>https:\/\/dottorcloud\.com\/funzioni\/<\/loc>/)
    assert.doesNotMatch(sitemap, /grazie|errore|404/)
  })

  test('a preview is kept out of search engines', () => {
    const preview = fs.mkdtempSync(path.join(os.tmpdir(), 'sito-anteprima-'))
    try {
      const run = spawnSync(process.execPath, [path.join(SITE, 'build.mjs')], {
        env: {
          ...process.env,
          SITO_DIST: preview,
          SITO_URL: 'https://dottorcloud.preview.npm2solutions.com',
          SITO_ANTEPRIMA: '1',
        },
        encoding: 'utf8',
      })
      assert.equal(run.status, 0, run.stderr)
      assert.equal(
        fs.readFileSync(path.join(preview, 'robots.txt'), 'utf8'),
        'User-agent: *\nDisallow: /\n',
      )
      const home = fs.readFileSync(path.join(preview, 'index.html'), 'utf8')
      assert.match(home, /<meta name="robots" content="noindex" \/>/)
      assert.match(
        home,
        /<link rel="canonical" href="https:\/\/dottorcloud\.preview\.npm2solutions\.com\/" \/>/,
      )
    } finally {
      fs.rmSync(preview, { recursive: true, force: true })
    }
  })
})

describe('the pages', () => {
  before(() => assert.equal(built.status, 0, built.stderr))

  test('have a title, a description, a canonical address and one <h1>', () => {
    for (const file of pages()) {
      const html = fs.readFileSync(file, 'utf8')
      const name = path.relative(OUT, file)
      assert.match(html, /<title>[^<]{10,}<\/title>/, `${name}: title`)
      assert.match(
        html,
        /<meta name="description" content="[^"]{50,}"/,
        `${name}: description`,
      )
      assert.match(
        html,
        /<link rel="canonical" href="https:\/\/dottorcloud\.com\//,
        `${name}: canonical`,
      )
      assert.equal(html.match(/<h1[\s>]/g)?.length, 1, `${name}: one <h1>`)
      assert.match(html, /<html lang="it">/, `${name}: language`)
    }
  })

  test('link only to pages, anchors and files that exist', () => {
    for (const file of pages()) {
      const html = fs.readFileSync(file, 'utf8')
      const name = path.relative(OUT, file)
      for (const [, attr, url] of html.matchAll(
        /\s(href|src|poster|action)="([^"]+)"/g,
      )) {
        if (/^(https?:|mailto:|tel:)/.test(url)) continue
        if (url.startsWith('#')) {
          const id = url.slice(1)
          if (id)
            assert.match(
              html,
              new RegExp(`id="${id}"`),
              `${name}: ${url} points nowhere`,
            )
          continue
        }
        assert.ok(
          url.startsWith('/'),
          `${name}: ${attr}="${url}" should start from the root`,
        )
        assert.ok(fs.existsSync(target(url)), `${name}: ${url} does not exist`)
        const anchor = url.split('#')[1]
        if (anchor) {
          const other = fs.readFileSync(target(url), 'utf8')
          assert.match(
            other,
            new RegExp(`id="${anchor}"`),
            `${name}: ${url} has no such anchor`,
          )
        }
      }
    }
  })

  test('describe every image, and give it its size', () => {
    for (const file of pages()) {
      const html = fs.readFileSync(file, 'utf8')
      for (const [tag] of html.matchAll(/<img\b[^>]*>/g)) {
        assert.match(tag, /\salt="/, `${path.relative(OUT, file)}: ${tag}`)
        assert.match(
          tag,
          /\swidth="\d+" height="\d+"/,
          `${path.relative(OUT, file)}: ${tag}`,
        )
      }
    }
  })

  test('show no price, plan or fee', () => {
    const money =
      /€|\beuro\b|\bprezz[io]|\blistin[oi]\b|\btariff|\bcost[aio]\b|\bcanone|al mese|\/mese|\bgratis|\bgratuit|\bpiano (base|pro|premium|start)/i
    for (const file of pages()) {
      const words = text(fs.readFileSync(file, 'utf8'))
      assert.doesNotMatch(words, money, path.relative(OUT, file))
    }
  })

  test('call the product DottorCloud and never by the framework it is built on', () => {
    for (const file of pages()) {
      assert.doesNotMatch(
        fs.readFileSync(file, 'utf8'),
        /frappe/i,
        path.relative(OUT, file),
      )
    }
  })

  test('load nothing from other sites', () => {
    for (const file of pages()) {
      const html = fs.readFileSync(file, 'utf8')
      for (const [tag] of html.matchAll(
        /<(?:script|img|source|video|iframe|link)\b[^>]*>/g,
      )) {
        if (/rel="canonical"/.test(tag)) continue
        assert.doesNotMatch(
          tag,
          /\s(?:src|href|poster)="(?:https?:)?\/\//,
          `${path.relative(OUT, file)}: ${tag}`,
        )
      }
    }
    const css = fs.readFileSync(path.join(OUT, 'css/sito.css'), 'utf8')
    assert.doesNotMatch(css, /url\(["']?(?:https?:)?\/\//)
    assert.doesNotMatch(css, /@import/)
  })
})

// --- the demo form ---

const php = spawnSync('php', ['-v']).status === 0
const mails = path.join(OUT, 'posta.txt')
const settings = path.join(OUT, 'sito.ini')
const counters = fs.mkdtempSync(path.join(os.tmpdir(), 'sito-contatori-'))
const archive = path.join(counters, 'richieste.jsonl')
let server
let base

async function post(fields, { json = true } = {}) {
  const body = new URLSearchParams(fields)
  return fetch(`${base}/api/richiesta-demo.php`, {
    method: 'POST',
    body,
    redirect: 'manual',
    headers: json ? { Accept: 'application/json' } : {},
  })
}

const good = {
  nome: 'Anna Bianchi',
  centro: 'Centro Medico Aurora',
  email: 'anna@aurora.example',
  telefono: '+39 02 1234 5678',
  tipo: 'Poliambulatorio',
  professionisti: '4-8',
  citta: 'Milano',
  messaggio: 'Vorremmo vedere le agende\ne il Sistema TS.',
  privacy: '1',
  t: '9000',
}

describe('the demo form', { skip: !php && 'php is not installed' }, () => {
  before(async () => {
    assert.equal(built.status, 0, built.stderr)
    fs.writeFileSync(
      settings,
      `destinatario = "vendite@npm2.example"\nmittente = "sito@dottorcloud.example"\ncartella = "${counters}"\narchivio = "${archive}"\n`,
    )
    const port = 20000 + Math.floor(Math.random() * 20000)
    base = `http://127.0.0.1:${port}`
    // a sendmail that keeps what it is given in a file; PHP adds -f<sender>, which it ignores
    const sendmail = path.join(counters, 'sendmail.sh')
    fs.writeFileSync(sendmail, `#!/bin/sh\ncat >> '${mails}'\n`, {
      mode: 0o755,
    })
    server = spawn(
      'php',
      ['-d', `sendmail_path=${sendmail}`, '-S', `127.0.0.1:${port}`, '-t', OUT],
      {
        env: { ...process.env, SITO_CONFIG: settings },
        stdio: 'ignore',
      },
    )
    for (let tries = 0; tries < 50; tries++) {
      try {
        await fetch(`${base}/robots.txt`)
        return
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
    }
    throw new Error('php -S did not start')
  })

  after(() => {
    server?.kill()
    fs.rmSync(counters, { recursive: true, force: true })
  })

  test('only takes POST', async () => {
    const response = await fetch(`${base}/api/richiesta-demo.php`)
    assert.equal(response.status, 405)
  })

  test('emails a good request to NPM2, replying to who wrote', async () => {
    fs.rmSync(mails, { force: true })
    const response = await post(good)
    assert.equal(response.status, 200)
    assert.deepEqual(await response.json(), { ok: true })
    const mail = fs.readFileSync(mails, 'utf8')
    assert.match(mail, /^To: vendite@npm2\.example\r?$/m)
    assert.match(
      mail,
      /^From: "Sito DottorCloud" <sito@dottorcloud\.example>\r?$/m,
    )
    assert.match(mail, /^Reply-To: "Anna Bianchi" <anna@aurora\.example>\r?$/m)
    assert.match(mail, /^Subject: Richiesta demo: Centro Medico Aurora\r?$/m)
    assert.match(mail, /Professionisti: 4-8/)
    assert.match(
      mail,
      /Cosa vorrebbe vedere:\nVorremmo vedere le agende\ne il Sistema TS\./,
    )
    const kept = fs
      .readFileSync(archive, 'utf8')
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line))
    assert.equal(kept.at(-1).centro, 'Centro Medico Aurora')
  })

  test('says what is missing or wrong, field by field', async () => {
    const response = await post({
      ...good,
      nome: ' ',
      email: 'non-una-email',
      telefono: '12',
      privacy: '',
    })
    assert.equal(response.status, 422)
    const answer = await response.json()
    assert.equal(answer.ok, false)
    assert.deepEqual(Object.keys(answer.errori).sort(), [
      'email',
      'nome',
      'privacy',
      'telefono',
    ])
  })

  test('accepts only its own choices', async () => {
    const response = await post({
      ...good,
      tipo: 'Ospedale',
      professionisti: '1000',
    })
    assert.deepEqual(Object.keys((await response.json()).errori).sort(), [
      'professionisti',
      'tipo',
    ])
  })

  test('keeps new lines out of the email headers', async () => {
    fs.rmSync(mails, { force: true })
    const response = await post({
      ...good,
      nome: 'Anna\r\nBcc: tutti@example.com',
      centro: 'Aurora\nBcc: altri@example.com',
    })
    assert.equal(response.status, 200)
    const mail = fs.readFileSync(mails, 'utf8')
    assert.doesNotMatch(mail, /^Bcc:/im)
    assert.match(
      mail,
      /^Reply-To: "Anna Bcc: tutti@example\.com" <anna@aurora\.example>\r?$/m,
    )
  })

  test('pretends all went well with a machine, and sends nothing', async () => {
    fs.rmSync(mails, { force: true })
    for (const trap of [{ sito_web: 'https://spam.example' }, { t: '400' }]) {
      const response = await post({ ...good, ...trap })
      assert.equal(response.status, 200)
      assert.deepEqual(await response.json(), { ok: true })
    }
    assert.equal(fs.existsSync(mails), false)
  })

  test('without JavaScript, goes on to the thank-you or the error page', async () => {
    let response = await post(good, { json: false })
    assert.equal(response.status, 303)
    assert.equal(response.headers.get('location'), '/demo/grazie/')
    response = await post({ ...good, email: '' }, { json: false })
    assert.equal(response.status, 303)
    assert.equal(response.headers.get('location'), '/demo/errore/')
  })

  test('stops an address after five requests in an hour', async () => {
    // the requests above already counted: fill up to the limit, then one more
    let response
    for (let i = 0; i < 6; i++) response = await post(good)
    assert.equal(response.status, 429)
    assert.equal((await response.json()).ok, false)
  })
})
