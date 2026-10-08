// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The site, built in a temporary folder and checked: every link and image
// leads somewhere, every page has its title and one <h1>, no price and no
// framework's name slip in; then the demo form's PHP, run with `php -S`, on
// the cases that matter. Run with: node --test siti/dottorcloud/test/

import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { after, before, describe, test } from 'node:test'
import { fileURLToPath } from 'node:url'

import { INDEXNOW_KEY, changedSince, request } from '../indexnow.mjs'
import { faqs, headings, readingMinutes, slugify, trail } from '../seo.mjs'

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

  test('give images an address that changes with the file, and smaller copies', () => {
    const home = fs.readFileSync(path.join(OUT, 'index.html'), 'utf8')
    const hero = home.match(/<img\b[^>]*showcase__main[^>]*>/)[0]
    assert.match(hero, /src="\/img\/agenda\.webp\?v=[0-9a-f]{8}"/)
    const set = hero.match(/srcset="([^"]+)"/)[1].split(', ')
    assert.deepEqual(
      set.map((entry) => entry.split(' ')[1]),
      ['800w', '1200w', '2000w'],
    )
    for (const entry of set)
      assert.ok(fs.existsSync(target(entry.split(' ')[0])), entry)
    assert.match(hero, /\ssizes="[^"]+"/)
    for (const file of pages()) {
      const html = fs.readFileSync(file, 'utf8')
      for (const [, url] of html.matchAll(/\s(?:src|poster)="(\/img\/[^"]+)"/g))
        assert.match(url, /\?v=[0-9a-f]{8}$/, `${path.relative(OUT, file)}: ${url}`)
    }
  })

  test('tell IndexNow the pages changed, with its key on the site', () => {
    const key = path.join(OUT, `${INDEXNOW_KEY}.txt`)
    assert.equal(fs.readFileSync(key, 'utf8').trim(), INDEXNOW_KEY)
    const xml = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8')
    assert.equal(changedSince(xml, '2000-01-01').length, xml.match(/<url>/g).length)
    // a page with no date (not committed yet) always counts as changed
    const undated = [...xml.matchAll(/<url><loc>([^<]+)<\/loc><\/url>/g)].map((m) => m[1])
    assert.deepEqual(changedSince(xml, '2999-01-01'), undated)
    const sample = '<url><loc>https://a.it/x/</loc><lastmod>2026-10-02</lastmod></url>' +
      '<url><loc>https://a.it/y/</loc><lastmod>2026-09-30</lastmod></url>'
    assert.deepEqual(changedSince(sample, '2026-10-01'), ['https://a.it/x/'])
    const body = request('https://dottorcloud.com', ['https://dottorcloud.com/'])
    assert.equal(body.host, 'dottorcloud.com')
    assert.equal(body.keyLocation, `https://dottorcloud.com/${INDEXNOW_KEY}.txt`)
  })

  test('show no price, plan or fee', () => {
    const money =
      /€|\beuro\b|\bprezz[io]|\blistin[oi]\b|\btariff|\bcost[aio]\b|\bcanone|al mese|\/mese|\bgratis|\bgratuit|\bpiano (base|pro|premium|start)/i
    // the articles and the glossary quote the law's amounts (the stamp duty,
    // the fines): they are checked for the product's own price only
    const editorial = (file) =>
      /^(approfondimenti|glossario)\//.test(path.relative(OUT, file))
    for (const file of pages()) {
      const words = text(fs.readFileSync(file, 'utf8'))
      if (editorial(file))
        assert.doesNotMatch(
          words,
          /DottorCloud (costa|a partire da)|prezz[io] di DottorCloud|\bpiano (base|pro|premium|start)/i,
          path.relative(OUT, file),
        )
      else assert.doesNotMatch(words, money, path.relative(OUT, file))
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

describe('what search engines read', () => {
  const html = (file) => fs.readFileSync(file, 'utf8')
  const indexed = () =>
    pages().filter((file) => !/name="robots" content="noindex"/.test(html(file)))
  const graph = (file) => {
    const scripts = [...html(file).matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
    assert.equal(scripts.length, 1, `${path.relative(OUT, file)}: one JSON-LD block`)
    return JSON.parse(scripts[0][1])['@graph']
  }
  const ofType = (nodes, type) => nodes.filter((n) => n['@type'] === type)

  test('every page to index has a short title and a description Google shows whole', () => {
    for (const file of indexed()) {
      const page = html(file)
      const title = page.match(/<title>([^<]*)<\/title>/)[1]
      const description = page
        .match(/<meta name="description" content="([^"]*)"/)[1]
        .replace(/&#39;|&apos;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
      const where = path.relative(OUT, file)
      assert.ok(title.length <= 65, `${where}: the title has ${title.length} characters`)
      assert.ok(
        description.length >= 70 && description.length <= 160,
        `${where}: the description has ${description.length} characters`,
      )
    }
  })

  test('every page says who we are, and where it sits', () => {
    for (const file of pages()) {
      const nodes = graph(file)
      const where = path.relative(OUT, file)
      assert.equal(ofType(nodes, 'Organization').length, 1, where)
      assert.equal(ofType(nodes, 'WebSite').length, 1, where)
      const canonical = html(file).match(/<link rel="canonical" href="([^"]+)"/)[1]
      if (canonical === 'https://dottorcloud.com/') continue
      const [crumbs] = ofType(nodes, 'BreadcrumbList')
      assert.ok(crumbs, `${where}: breadcrumbs`)
      const items = crumbs.itemListElement
      assert.equal(items[0].item, 'https://dottorcloud.com/', where)
      assert.equal(items.at(-1).item, canonical, where)
    }
  })

  test('the questions of a page are its FAQ', () => {
    for (const file of pages()) {
      const asked = (html(file).match(/<details\b/g) || []).length
      if (!asked) continue
      const nodes = graph(file)
      const faq = nodes.find((n) => n['@type'] === 'FAQPage') || nodes.find((n) => n.mainEntity)
      assert.ok(faq, path.relative(OUT, file))
      assert.equal(faq.mainEntity.length, asked, path.relative(OUT, file))
    }
  })

  test('the product is described on the home and on each kind of centre', () => {
    for (const where of ['', 'gestionale-poliambulatorio', 'gestionale-studio-medico', 'gestionale-fisioterapia', 'gestionale-nutrizionista', 'gestionale-studio-dentistico']) {
      const nodes = graph(path.join(OUT, where, 'index.html'))
      assert.equal(ofType(nodes, 'SoftwareApplication').length, 1, where || 'home')
    }
  })

  test('an article has its date, its section, its table of contents and its readers', () => {
    const dir = path.join(OUT, 'approfondimenti')
    const articles = fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory())
      .map((e) => path.join(dir, e.name, 'index.html'))
    assert.ok(articles.length >= 8, `${articles.length} articles`)
    for (const file of articles) {
      const page = html(file)
      const where = path.relative(OUT, file)
      const [post] = ofType(graph(file), 'BlogPosting')
      assert.ok(post, where)
      assert.match(post.datePublished, /^\d{4}-\d{2}-\d{2}$/, where)
      assert.ok(post.wordCount > 500, `${where}: ${post.wordCount} words`)
      assert.match(page, /<meta property="og:type" content="article" \/>/, where)
      assert.match(page, /<nav class="toc"/, where)
      assert.match(page, /class="breadcrumb"/, where)
      // an article on the rules says where they come from, and that it is not advice
      if (post.articleSection === 'Norme') {
        assert.match(page, /<section class="sources">/, where)
        assert.match(page, /class="disclaimer"/, where)
      }
    }
  })

  test('the glossary defines its terms', () => {
    const file = path.join(OUT, 'glossario', 'index.html')
    const [set] = ofType(graph(file), 'DefinedTermSet')
    assert.equal(set.hasDefinedTerm.length, (html(file).match(/<dt\b/g) || []).length)
  })

  test('the sitemap lists every page to index, the feed every article', () => {
    const sitemap = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8')
    for (const file of indexed()) {
      const canonical = html(file).match(/<link rel="canonical" href="([^"]+)"/)[1]
      assert.ok(sitemap.includes(`<loc>${canonical}</loc>`), canonical)
    }
    assert.match(sitemap, /approfondimenti\/ridurre-le-visite-saltate\/<\/loc><lastmod>\d{4}-\d{2}-\d{2}<\/lastmod>/)
    const feed = fs.readFileSync(path.join(OUT, 'approfondimenti', 'feed.xml'), 'utf8')
    const items = (feed.match(/<item>/g) || []).length
    const articles = fs.readdirSync(path.join(OUT, 'approfondimenti'), { withFileTypes: true }).filter((e) => e.isDirectory()).length
    assert.equal(items, articles)
    assert.ok(fs.existsSync(path.join(OUT, 'llms.txt')))
  })
})

describe('the pieces of seo.mjs', () => {
  test('slugify keeps letters and numbers, without accents', () => {
    assert.equal(slugify('Perché il Sistema TS è annuale?'), 'perche-il-sistema-ts-e-annuale')
  })

  test('every heading gets an id once, and the table of contents follows', () => {
    const { html, toc } = headings('<h2>Uno</h2><p>x</p><h2>Uno</h2><h2 id="tre">Tre</h2>')
    assert.deepEqual(toc.map((h) => h.id), ['uno', 'uno-2', 'tre'])
    assert.match(html, /<h2 id="uno-2">Uno<\/h2>/)
  })

  test('the FAQ is read from the questions on the page', () => {
    const out = faqs('<details><summary>Si può? <svg><path/></svg></summary><p>Sì, <b>certo</b>.</p></details>')
    assert.deepEqual(out, [{ question: 'Si può?', answer: 'Sì, certo .' }])
  })

  test('the trail goes from the home page through the parents', () => {
    const pages = [
      { path: '/', title: 'DottorCloud · Il gestionale' },
      { path: '/approfondimenti/', title: 'Approfondimenti · DottorCloud', crumb: 'Approfondimenti' },
      { path: '/approfondimenti/x/', title: 'X · DottorCloud', parent: '/approfondimenti/', crumb: 'X' },
    ]
    const byPath = new Map(pages.map((p) => [p.path, p]))
    assert.deepEqual(trail(pages[2], byPath).map((c) => c.name), ['Home', 'Approfondimenti', 'X'])
  })

  test('reading takes at least a minute', () => {
    assert.equal(readingMinutes('<p>poche parole</p>'), 1)
    assert.equal(readingMinutes(`<p>${'parola '.repeat(1000)}</p>`), 5)
  })
})

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
