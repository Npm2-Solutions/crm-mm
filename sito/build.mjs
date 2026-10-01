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
// the design system go in front of the stylesheet: one source for each.
//
//   SITO_URL=https://dottorcloud.com   the address the site answers to
//   SITO_ANTEPRIMA=1                  a preview: noindex, and robots.txt says no
//   SITO_DIST=/some/folder            where to write (default sito/dist)

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

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
  'font/inter.woff2': 'brand/video/sorgenti/fonts/inter.woff2',
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

function sizeImages(html, file) {
  return html.replace(/<img\b([^>]*?)\s*\/?>/g, (tag, attrs) => {
    const src = attrs.match(/\ssrc="([^"]+)"/)?.[1]
    if (!src) throw new Error(`${file}: an <img> without src`)
    if (!/\salt="/.test(attrs)) throw new Error(`${file}: ${src} has no alt`)
    let extra = ''
    if (src.startsWith('/') && !/\swidth="/.test(attrs)) {
      const { width, height } = imageSize(path.join(OUT, src.split('?')[0]))
      extra += ` width="${width}" height="${height}"`
    }
    if (!/\sloading="/.test(attrs)) extra += ' loading="lazy"'
    if (!/\sdecoding="/.test(attrs)) extra += ' decoding="async"'
    return `<img${attrs}${extra} />`
  })
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
  const css = `${tokens}\n${read(path.join(SITE, 'risorse/css/sito.css'))}`
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
  const pages = []
  for (const name of fs.readdirSync(path.join(SITE, 'pagine')).sort()) {
    if (!name.endsWith('.html')) continue
    const file = path.join('pagine', name)
    const page = parsePage(read(path.join(SITE, file)), file)
    const noindex = PREVIEW || page.index === 'no'
    const values = {
      ...COMPANY,
      title: escape(page.title),
      description: escape(page.description),
      canonical: escape(ORIGIN + page.path),
      origin: ORIGIN,
      robots: noindex ? '<meta name="robots" content="noindex" />' : '',
      head: page.path === '/' ? organization() : '',
      version,
      year: String(new Date().getFullYear()),
    }
    values.content = render(page.content, page, values)
    let html = render(layout, page, values)
    const left = html.match(/\{\{[^}]*\}\}/)
    if (left) throw new Error(`${file}: ${left[0]} was not replaced`)
    html = sizeImages(html, file)
    const target = page.path.endsWith('/')
      ? path.join(OUT, page.path, 'index.html')
      : path.join(OUT, page.path)
    write(target, html)
    pages.push({ ...page, noindex })
  }

  write(
    path.join(OUT, 'robots.txt'),
    PREVIEW
      ? 'User-agent: *\nDisallow: /\n'
      : `User-agent: *\nDisallow: /api/\n\nSitemap: ${ORIGIN}/sitemap.xml\n`,
  )
  const listed = pages.filter((page) => !page.noindex)
  write(
    path.join(OUT, 'sitemap.xml'),
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      listed
        .map((page) => `  <url><loc>${ORIGIN}${page.path}</loc></url>\n`)
        .join('') +
      '</urlset>\n',
  )
  // the deploy script looks for this before it replaces a folder's contents
  write(path.join(OUT, '.sito-dottorcloud'), `${version}\n`)
  return pages
}

function organization() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: COMPANY.company,
    url: ORIGIN,
    logo: `${ORIGIN}/img/logo.svg`,
    email: COMPANY.email,
    vatID: COMPANY.vat,
    address: {
      '@type': 'PostalAddress',
      streetAddress: 'Via San Gregorio 55',
      postalCode: '20124',
      addressLocality: 'Milano',
      addressCountry: 'IT',
    },
    brand: { '@type': 'Brand', name: 'DottorCloud' },
  }
  return `<script type="application/ld+json">${JSON.stringify(data)}</script>`
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
