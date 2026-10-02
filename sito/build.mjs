#!/usr/bin/env node
// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Builds the DottorCloud website into sito/dist, with no dependencies:
//
//   node sito/build.mjs
//
// Each page in pagine/ goes inside parti/layout.html; {{> name}} pulls in a
// part, {{icon name}} a Lucide icon from risorse/icone, {{current key}} marks
// the menu's page. Images get their width and height from the file, so nothing
// jumps while they load. Logo, font and video come from brand/, the tokens of
// the design system go in front of the stylesheet and the brand's layer
// (brand/sito/sito-marchio.css) after it: one source for each.
//
//   SITO_URL=https://dottorcloud.com   the address the site answers to
//   SITO_ANTEPRIMA=1                  a preview: noindex, and robots.txt says no
//   SITO_DIST=/some/folder            where to write (default sito/dist)

import { execFileSync } from 'node:child_process'
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  breadcrumbHtml,
  feed,
  headings,
  italianDate,
  readingMinutes,
  sitemap,
  structuredData,
  trail,
  wordCount,
} from './seo.mjs'
import { INDEXNOW_KEY } from './indexnow.mjs'

const SITE = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.dirname(SITE)
const OUT = path.resolve(process.env.SITO_DIST || path.join(SITE, 'dist'))
const ORIGIN = (process.env.SITO_URL || 'https://dottorcloud.com').replace(
  /\/+$/,
  '',
)
const PREVIEW = process.env.SITO_ANTEPRIMA === '1'

// what the footer, the legal pages and the form say about the company
export const COMPANY = {
  company: 'NPM2 Solutions Srl',
  address: 'Via San Gregorio 55, 20124 Milano',
  street: 'Via San Gregorio 55',
  postalCode: '20124',
  city: 'Milano',
  vat: 'IT13832480969',
  email: 'info@npm2solutions.com',
}

// files that come from elsewhere in the repository: published path -> source
const FROM_REPO = {
  'img/logo.svg': 'brand/logo/dottorcloud-orizzontale.svg',
  'img/logo-negativo.svg': 'brand/logo/dottorcloud-orizzontale-negativo.svg',
  'img/marchio.svg': 'brand/logo/dottorcloud-marchio.svg',
  'favicon.svg': 'brand/logo/dottorcloud-icona-app.svg',
  'apple-touch-icon.png': 'crm/public/manifest/apple-icon-180.png',
  'font/inter.woff2': 'brand/font/Inter-Variable-latin.woff2',
  'img/stato-vuoto.svg': 'brand/composizioni/stato-vuoto.svg',
  'video/dottorcloud.mp4': 'brand/video/DottorCloud.mp4',
}

const read = (file) => fs.readFileSync(file, 'utf8')

/** Text that goes inside an attribute or a <title>. */
const escape = (text) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, content)
}

function copy(from, to) {
  fs.mkdirSync(path.dirname(to), { recursive: true })
  fs.copyFileSync(from, to)
}

function copyDir(from, to) {
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    const source = path.join(from, entry.name)
    if (entry.isDirectory()) copyDir(source, path.join(to, entry.name))
    else copy(source, path.join(to, entry.name))
  }
}

// --- pages ---

/** A page: the comment on top says what it is, the rest is its <main>. */
export function parsePage(source, file) {
  const match = source.match(/^<!--\n([\s\S]*?)\n-->\n/)
  if (!match)
    throw new Error(
      `${file}: the page starts with a comment of key: value lines`,
    )
  const meta = {}
  for (const line of match[1].split('\n')) {
    const at = line.indexOf(':')
    if (at < 1) throw new Error(`${file}: "${line}" is not key: value`)
    meta[line.slice(0, at).trim()] = line.slice(at + 1).trim()
  }
  for (const key of ['title', 'description', 'path']) {
    if (!meta[key]) throw new Error(`${file}: "${key}" is missing`)
  }
  return { ...meta, content: source.slice(match[0].length) }
}

const iconCache = new Map()

function icon(name, extraClass = '') {
  if (!iconCache.has(name)) {
    const file = path.join(SITE, 'risorse/icone', `${name}.svg`)
    if (!fs.existsSync(file))
      throw new Error(`icon "${name}" is not in risorse/icone`)
    iconCache.set(name, read(file).trim())
  }
  const classes = ['icon', extraClass].filter(Boolean).join(' ')
  return `<svg class="${classes}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${iconCache.get(name)}</svg>`
}

export function render(template, page, values, depth = 0) {
  if (depth > 8) throw new Error('parts include each other in a loop')
  let html = template.replace(/\{\{>\s*([\w-]+)\s*\}\}/g, (_, name) => {
    const file = path.join(SITE, 'parti', `${name}.html`)
    if (!fs.existsSync(file)) throw new Error(`part "${name}" is not in parti/`)
    return render(read(file), page, values, depth + 1)
  })
  html = html.replace(
    /\{\{icon ([\w-]+)(?: ([\w-]+))?\}\}/g,
    (_, name, extra) => icon(name, extra),
  )
  html = html.replace(/\{\{current ([\w-]+)\}\}/g, (_, key) =>
    page.nav === key ? 'aria-current="page"' : '',
  )
  return html.replace(/\{\{(\w+)\}\}/g, (whole, key) =>
    key in values ? values[key] : whole,
  )
}

// --- images: width and height from the file ---

export function imageSize(file) {
  const data = fs.readFileSync(file)
  const ext = path.extname(file).toLowerCase()
  if (ext === '.png')
    return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) }
  if (ext === '.webp') {
    const chunk = data.toString('ascii', 12, 16)
    if (chunk === 'VP8X')
      return {
        width: 1 + data.readUIntLE(24, 3),
        height: 1 + data.readUIntLE(27, 3),
      }
    if (chunk === 'VP8L') {
      const bits = data.readUInt32LE(21)
      return { width: 1 + (bits & 0x3fff), height: 1 + ((bits >> 14) & 0x3fff) }
    }
    if (chunk === 'VP8 ')
      return {
        width: data.readUInt16LE(26) & 0x3fff,
        height: data.readUInt16LE(28) & 0x3fff,
      }
  }
  if (ext === '.svg') {
    const box = data
      .toString('utf8')
      .match(/viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"/)
    if (box) return { width: Math.round(+box[1]), height: Math.round(+box[2]) }
  }
  throw new Error(`cannot read the size of ${file}`)
}

const versions = new Map()
// an address with the file's fingerprint: /img/agenda.webp?v=1a2b3c4d
export function versioned(src) {
  if (!versions.has(src)) {
    const data = fs.readFileSync(path.join(OUT, src))
    const hash = crypto.createHash('sha256').update(data).digest('hex')
    versions.set(src, `${src}?v=${hash.slice(0, 8)}`)
  }
  return versions.get(src)
}

// agenda.webp -> agenda-800.webp, agenda-1200.webp, smallest first
function smallerCopies(file) {
  const dir = path.dirname(file)
  const ext = path.extname(file)
  const base = path.basename(file, ext)
  const pattern = new RegExp(`^${base}-(\\d+)${ext.replace('.', '\\.')}$`)
  const prefix = path.posix.dirname(path.relative(OUT, file).split(path.sep).join('/'))
  return fs
    .readdirSync(dir)
    .map((name) => [name, name.match(pattern)])
    .filter(([, match]) => match)
    .map(([name, match]) => ({ src: `/${prefix}/${name}`, width: +match[1] }))
    .sort((a, b) => a.width - b.width)
}

function sizeImages(html, file) {
  return html.replace(/<img\b([^>]*?)\s*\/?>/g, (tag, attrs) => {
    const src = attrs.match(/\ssrc="([^"]+)"/)?.[1]
    if (!src) throw new Error(`${file}: an <img> without src`)
    if (!/\salt="/.test(attrs)) throw new Error(`${file}: ${src} has no alt`)
    let extra = ''
    if (src.startsWith('/') && !src.includes('?')) {
      const local = path.join(OUT, src)
      const { width, height } = imageSize(local)
      if (!/\swidth="/.test(attrs))
        extra += ` width="${width}" height="${height}"`
      // the server keeps images for years: a new file gets a new address
      attrs = attrs.replace(/\ssrc="[^"]+"/, ` src="${versioned(src)}"`)
      const smaller = smallerCopies(local)
      if (smaller.length && !/\ssrcset="/.test(attrs)) {
        const set = [...smaller, { src, width }]
          .map((copy) => `${versioned(copy.src)} ${copy.width}w`)
          .join(', ')
        // the pictures are made at twice the widest the page shows them
        const sizes =
          attrs.match(/\ssizes="([^"]+)"/)?.[1] ??
          `(max-width: 900px) calc(100vw - 32px), ${Math.round(width / 2)}px`
        attrs = attrs.replace(/\ssizes="[^"]+"/, '')
        extra += ` srcset="${set}" sizes="${sizes}"`
      }
    }
    if (!/\sloading="/.test(attrs)) extra += ' loading="lazy"'
    if (!/\sdecoding="/.test(attrs)) extra += ' decoding="async"'
    return `<img${attrs}${extra} />`
  }).replace(/\sposter="(\/[^"?]+)"/g, (_, src) => ` poster="${versioned(src)}"`)
}

// --- favicon.ico: the 32px PNG inside an ICO container ---

function ico(png) {
  const { width, height } = {
    width: png.readUInt32BE(16),
    height: png.readUInt32BE(20),
  }
  const head = Buffer.alloc(22)
  head.writeUInt16LE(0, 0) // reserved
  head.writeUInt16LE(1, 2) // icon
  head.writeUInt16LE(1, 4) // one image
  head.writeUInt8(width >= 256 ? 0 : width, 6)
  head.writeUInt8(height >= 256 ? 0 : height, 7)
  head.writeUInt8(0, 8) // no palette
  head.writeUInt8(0, 9)
  head.writeUInt16LE(1, 10) // planes
  head.writeUInt16LE(32, 12) // bits per pixel
  head.writeUInt32LE(png.length, 14)
  head.writeUInt32LE(22, 18) // where the image starts
  return Buffer.concat([head, png])
}

// --- the build ---

export function build() {
  fs.rmSync(OUT, { recursive: true, force: true })
  versions.clear()
  fs.mkdirSync(OUT, { recursive: true })

  // static files first: the pages measure the images in OUT
  copyDir(path.join(SITE, 'risorse/img'), path.join(OUT, 'img'))
  for (const [to, from] of Object.entries(FROM_REPO))
    copy(path.join(ROOT, from), path.join(OUT, to))
  write(
    path.join(OUT, 'favicon.ico'),
    ico(fs.readFileSync(path.join(ROOT, 'brand/logo/png/favicon-32.png'))),
  )
  copyDir(path.join(SITE, 'api'), path.join(OUT, 'api'))

  const tokens = read(path.join(ROOT, 'brand/design-system/tokens.css'))
  // the brand's layer goes last: it restyles the site without touching its rules
  const layer = read(path.join(ROOT, 'brand/sito/sito-marchio.css'))
  const css = `${tokens}\n${read(path.join(SITE, 'risorse/css/sito.css'))}\n${layer}`
  const js = read(path.join(SITE, 'risorse/js/sito.js'))
  write(path.join(OUT, 'css/sito.css'), css)
  write(path.join(OUT, 'js/sito.js'), js)
  const version = crypto
    .createHash('sha256')
    .update(css)
    .update(js)
    .digest('hex')
    .slice(0, 10)

  const layout = read(path.join(SITE, 'parti/layout.html'))

  // every page first, so breadcrumbs and lists can name the others
  const pages = []
  for (const name of fs.readdirSync(path.join(SITE, 'pagine')).sort()) {
    if (!name.endsWith('.html')) continue
    const file = path.join('pagine', name)
    pages.push({ ...parsePage(read(path.join(SITE, file)), file), file })
  }
  const articles = readArticles()
  pages.push(...articles)
  const byPath = new Map(pages.map((page) => [page.path, page]))
  for (const page of pages) {
    if (page.parent && !byPath.has(page.parent))
      throw new Error(`${page.file}: its parent ${page.parent} is not a page`)
  }

  const listed = articles.filter((a) => a.index !== 'no')
  const shared = {
    elenco_articoli: articleList(listed),
    ultimi_articoli: articleCards(listed.slice(0, 3)),
  }
  const image = `${ORIGIN}/img/condivisione.jpg`

  for (const page of pages) {
    const noindex = PREVIEW || page.index === 'no'
    const crumbs = trail(page, byPath)
    const values = {
      ...COMPANY,
      ...shared,
      title: escape(page.title),
      description: escape(page.description),
      canonical: escape(ORIGIN + page.path),
      origin: ORIGIN,
      robots: noindex ? '<meta name="robots" content="noindex" />' : '',
      breadcrumb: breadcrumbHtml(crumbs),
      ogtype: page.article ? 'article' : 'website',
      ogextra: page.article
        ? [
            `<meta property="article:published_time" content="${page.date}" />`,
            `<meta property="article:modified_time" content="${page.updated || page.date}" />`,
            `<meta property="article:section" content="${escape(page.category)}" />`,
          ].join('\n    ')
        : '',
      version,
      year: String(new Date().getFullYear()),
    }
    let content = page.content
    if (page.article) content = articleContent(page, articles, values)
    values.content = render(content, page, values)
    values.head = structuredData({
      origin: ORIGIN,
      page: { ...page, product: page.product === 'yes' || page.path === '/' },
      crumbs,
      html: values.content,
      company: COMPANY,
      logo: `${ORIGIN}/img/logo.svg`,
      image,
    })
    let html = render(layout, page, values)
    const left = html.match(/\{\{[^}]*\}\}/)
    if (left) throw new Error(`${page.file}: ${left[0]} was not replaced`)
    html = sizeImages(html, page.file)
    const target = page.path.endsWith('/')
      ? path.join(OUT, page.path, 'index.html')
      : path.join(OUT, page.path)
    write(target, html)
    page.noindex = noindex
    page.lastmod =
      page.updated || page.date || lastChange(path.join(SITE, page.file))
  }

  write(
    path.join(OUT, 'robots.txt'),
    PREVIEW
      ? 'User-agent: *\nDisallow: /\n'
      : `User-agent: *\nDisallow: /api/\n\nSitemap: ${ORIGIN}/sitemap.xml\n`,
  )
  write(
    path.join(OUT, 'sitemap.xml'),
    sitemap(
      ORIGIN,
      pages.filter((page) => !page.noindex),
    ),
  )
  write(path.join(OUT, 'approfondimenti/feed.xml'), feed(ORIGIN, listed))
  write(
    path.join(OUT, 'llms.txt'),
    llms(pages.filter((page) => !page.noindex)),
  )
  // IndexNow's proof of ownership (sito/indexnow.mjs), never on a preview
  if (!PREVIEW) write(path.join(OUT, `${INDEXNOW_KEY}.txt`), `${INDEXNOW_KEY}\n`)
  // the deploy script looks for this before it replaces a folder's contents
  write(path.join(OUT, '.sito-dottorcloud'), `${version}\n`)
  return pages
}

// --- articles: sito/approfondimenti/<slug>.html, newest first ---

export const CATEGORIES = ['Guide', 'Norme', 'Organizzazione']

function readArticles() {
  const dir = path.join(SITE, 'approfondimenti')
  if (!fs.existsSync(dir)) return []
  const out = []
  for (const name of fs.readdirSync(dir).sort()) {
    if (!name.endsWith('.html')) continue
    const file = path.join('approfondimenti', name)
    const page = parsePage(
      read(path.join(SITE, file)).replace(
        /^<!--\n/,
        `<!--\npath: /approfondimenti/${name.replace(/\.html$/, '')}/\n`,
      ),
      file,
    )
    for (const key of ['headline', 'category', 'date', 'summary']) {
      if (!page[key]) throw new Error(`${file}: "${key}" is missing`)
    }
    if (!CATEGORIES.includes(page.category))
      throw new Error(
        `${file}: the category is one of ${CATEGORIES.join(', ')}`,
      )
    for (const key of ['date', 'updated']) {
      if (page[key] && !/^\d{4}-\d{2}-\d{2}$/.test(page[key]))
        throw new Error(`${file}: ${key} is YYYY-MM-DD`)
    }
    const { html, toc } = headings(page.content)
    out.push({
      ...page,
      file,
      content: html,
      toc,
      article: true,
      nav: 'approfondimenti',
      parent: '/approfondimenti/',
      crumb: page.crumb || page.headline,
      words: wordCount(html),
      minutes: readingMinutes(html),
    })
  }
  return out.sort((a, b) => (b.date + b.path).localeCompare(a.date + a.path))
}

function articleContent(page, articles, values) {
  const toc = page.toc.length
    ? `<nav class="toc" aria-label="In questo articolo"><p>In questo articolo</p><ol role="list">${page.toc
        .map((h) => `<li><a href="#${h.id}">${escape(h.text)}</a></li>`)
        .join('')}</ol></nav>`
    : ''
  const others = articles.filter((a) => a !== page && a.index !== 'no')
  const related = [
    ...others.filter((a) => a.category === page.category),
    ...others.filter((a) => a.category !== page.category),
  ].slice(0, 3)
  const when =
    page.updated && page.updated !== page.date
      ? `Aggiornato il <time datetime="${page.updated}">${italianDate(page.updated)}</time>`
      : `<time datetime="${page.date}">${italianDate(page.date)}</time>`
  const fill = {
    ...values,
    headline: escape(page.headline),
    summary: escape(page.summary),
    category: escape(page.category),
    meta: `${when} · ${page.minutes} min di lettura · Redazione DottorCloud`,
    toc,
    body: render(page.content, page, values),
    related: articleCards(related),
  }
  return render(read(path.join(SITE, 'parti/articolo.html')), page, fill)
}

function articleCard(a) {
  return `<article class="card post-card">
  <span class="post-card__category">${escape(a.category)}</span>
  <h3><a href="${a.path}">${escape(a.headline)}</a></h3>
  <p>${escape(a.summary)}</p>
  <p class="post-card__meta"><time datetime="${a.date}">${italianDate(a.date)}</time> · ${a.minutes} min</p>
</article>`
}

function articleCards(list) {
  return `<div class="grid grid--3 post-grid">${list.map(articleCard).join('\n')}</div>`
}

/** The index: the articles by category, each category with its anchor. */
function articleList(list) {
  return CATEGORIES.filter((c) => list.some((a) => a.category === c))
    .map((c) => {
      const id = c.toLowerCase()
      return `<section class="post-group" id="${id}" aria-labelledby="gruppo-${id}">
  <h2 id="gruppo-${id}" class="h3">${c}</h2>
  ${articleCards(list.filter((a) => a.category === c))}
</section>`
    })
    .join('\n')
}

// --- dates and the summary for assistants ---

const changes = new Map()

/** The day a file last changed, from git; nothing outside a repository. */
function lastChange(file) {
  if (!changes.has(file)) {
    let day = ''
    try {
      day = execFileSync('git', ['log', '-1', '--format=%cs', '--', file], {
        cwd: SITE,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore'],
      }).trim()
    } catch {
      day = ''
    }
    changes.set(file, day)
  }
  return changes.get(file)
}

/** llms.txt: what the site is and its pages, for assistants that read it. */
function llms(pages) {
  const line = (p) =>
    `- [${p.headline || p.title.replace(/\s*·\s*DottorCloud$/, '')}](${ORIGIN}${p.path}): ${p.description}`
  const main = pages.filter((p) => !p.article)
  const posts = pages.filter((p) => p.article)
  return `# DottorCloud

> Il gestionale per i centri medici di NPM2 Solutions Srl: agenda per medici, stanze e attrezzature, cartella clinica, fatture con il Sistema TS, WhatsApp, telefono, marketing e l'app per i pazienti. Ognuno vede solo quello che gli serve. Il sito non pubblica prezzi: si richiede una demo.

## Pagine

${main.map(line).join('\n')}

## Approfondimenti

${posts.map(line).join('\n')}
`
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const pages = build()
  console.log(
    `${pages.length} pages in ${path.relative(process.cwd(), OUT) || OUT} (${ORIGIN}${PREVIEW ? ', preview' : ''})`,
  )
}
