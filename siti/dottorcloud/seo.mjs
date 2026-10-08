// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// What search engines read besides the words: the structured data of every
// page (schema.org as JSON-LD), the breadcrumbs, the questions of a page as an
// FAQ, the articles' dates and table of contents, the sitemap and the feed.
// Pure functions on strings: build.mjs hands them the pages, the tests too.

const MONTHS = new Intl.DateTimeFormat('it-IT', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
})

/** 2026-10-02 → "2 ottobre 2026". */
export function italianDate(iso) {
  return MONTHS.format(new Date(`${iso}T00:00:00Z`))
}

/** 2026-10-02 → "Fri, 02 Oct 2026 08:00:00 GMT", as RSS wants it. */
export function rssDate(iso) {
  return new Date(`${iso}T08:00:00Z`).toUTCString()
}

/** Words of some HTML, without its tags. */
export function plainText(html) {
  return html
    .replace(/<(script|style)[\s\S]*?<\/\1>/g, ' ')
    .replace(/<svg[\s\S]*?<\/svg>/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&rsquo;/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
}

export function wordCount(html) {
  const text = plainText(html)
  return text ? text.split(' ').length : 0
}

/** Minutes to read, at 200 words a minute, at least one. */
export function readingMinutes(html) {
  return Math.max(1, Math.round(wordCount(html) / 200))
}

/** "Sistema TS: chi invia" → "sistema-ts-chi-invia". */
export function slugify(text) {
  return plainText(text)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/**
 * Gives every <h2> of an article an id (unless it has one) and returns the
 * headings for the table of contents.
 */
export function headings(html) {
  const toc = []
  const used = new Set()
  const out = html.replace(/<h2(\s[^>]*)?>([\s\S]*?)<\/h2>/g, (whole, attrs = '', inner) => {
    let id = attrs.match(/\sid="([^"]+)"/)?.[1]
    if (!id) {
      id = slugify(inner) || 'sezione'
      let n = 2
      while (used.has(id)) id = `${slugify(inner)}-${n++}`
    }
    used.add(id)
    toc.push({ id, text: plainText(inner) })
    return attrs.includes(' id="') ? whole : `<h2 id="${id}"${attrs}>${inner}</h2>`
  })
  return { html: out, toc }
}

/** The questions and answers of a page's FAQ (`.faq details`). */
export function faqs(html) {
  const out = []
  for (const block of html.matchAll(/<details\b[^>]*>([\s\S]*?)<\/details>/g)) {
    const question = block[1].match(/<summary\b[^>]*>([\s\S]*?)<\/summary>/)
    if (!question) continue
    const answer = block[1].slice(question.index + question[0].length)
    const q = plainText(question[1])
    const a = plainText(answer)
    if (q && a) out.push({ question: q, answer: a })
  }
  return out
}

/** The terms of a glossary: <dt id="…">term</dt><dd>definition</dd>. */
export function terms(html) {
  const out = []
  for (const m of html.matchAll(/<dt\b[^>]*\sid="([^"]+)"[^>]*>([\s\S]*?)<\/dt>\s*<dd\b[^>]*>([\s\S]*?)<\/dd>/g)) {
    out.push({ id: m[1], name: plainText(m[2]), description: plainText(m[3]) })
  }
  return out
}

/** The trail from the home page to a page: [{name, path}]. */
export function trail(page, byPath) {
  const crumbs = []
  let at = page
  const seen = new Set()
  while (at && !seen.has(at.path)) {
    seen.add(at.path)
    crumbs.unshift({ name: at.crumb || shortTitle(at.title), path: at.path })
    at = at.parent ? byPath.get(at.parent) : null
  }
  if (crumbs[0]?.path !== '/') crumbs.unshift({ name: 'Home', path: '/' })
  else crumbs[0].name = 'Home'
  return crumbs
}

/** "Per chi è · DottorCloud" → "Per chi è". */
export function shortTitle(title) {
  return title.replace(/\s*[·|–-]\s*DottorCloud\s*$/, '').trim()
}

const escapeHtml = (text) =>
  text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** The breadcrumbs as the visitor sees them. */
export function breadcrumbHtml(crumbs) {
  const items = crumbs.map((crumb, i) =>
    i === crumbs.length - 1
      ? `<li><span aria-current="page">${escapeHtml(crumb.name)}</span></li>`
      : `<li><a href="${crumb.path}">${escapeHtml(crumb.name)}</a></li>`,
  )
  return `<nav class="breadcrumb" aria-label="Percorso"><ol role="list">${items.join('')}</ol></nav>`
}

/**
 * The structured data of a page, one @graph: the company, the site, the page
 * with its breadcrumbs, and what the page is about (the product, an FAQ, an
 * article, a glossary).
 */
export function structuredData({ origin, page, crumbs, html, company, logo, image }) {
  const url = origin + page.path
  const org = {
    '@type': 'Organization',
    '@id': `${origin}/#organizzazione`,
    name: company.company,
    url: `${origin}/`,
    logo: { '@type': 'ImageObject', url: logo },
    email: company.email,
    vatID: company.vat,
    address: {
      '@type': 'PostalAddress',
      streetAddress: company.street,
      postalCode: company.postalCode,
      addressLocality: company.city,
      addressCountry: 'IT',
    },
    brand: { '@type': 'Brand', name: 'DottorCloud' },
  }
  const website = {
    '@type': 'WebSite',
    '@id': `${origin}/#sito`,
    url: `${origin}/`,
    name: 'DottorCloud',
    inLanguage: 'it-IT',
    publisher: { '@id': org['@id'] },
  }
  const graph = [org, website]
  const webpage = {
    '@type': 'WebPage',
    '@id': `${url}#pagina`,
    url,
    name: shortTitle(page.title),
    description: page.description,
    inLanguage: 'it-IT',
    isPartOf: { '@id': website['@id'] },
    primaryImageOfPage: { '@type': 'ImageObject', url: image },
  }
  graph.push(webpage)

  if (crumbs.length > 1) {
    const list = {
      '@type': 'BreadcrumbList',
      '@id': `${url}#percorso`,
      itemListElement: crumbs.map((crumb, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: crumb.name,
        item: origin + crumb.path,
      })),
    }
    webpage.breadcrumb = { '@id': list['@id'] }
    graph.push(list)
  }

  if (page.product) {
    graph.push({
      '@type': 'SoftwareApplication',
      '@id': `${origin}/#dottorcloud`,
      name: 'DottorCloud',
      url: `${origin}/`,
      description:
        'Il gestionale per i centri medici: agenda, cartella clinica, fatture con il Sistema TS, WhatsApp, telefono, marketing e l\'app per i pazienti.',
      applicationCategory: 'BusinessApplication',
      applicationSubCategory: 'Gestionale per centri medici',
      operatingSystem: 'Web, iOS, Android',
      inLanguage: 'it-IT',
      image,
      publisher: { '@id': org['@id'] },
      audience: { '@type': 'Audience', audienceType: page.audience || 'Centri medici e studi sanitari' },
    })
    webpage.about = { '@id': `${origin}/#dottorcloud` }
  }

  const questions = faqs(html)
  if (questions.length) {
    webpage['@type'] = page.article ? 'WebPage' : 'FAQPage'
    const entities = questions.map((q) => ({
      '@type': 'Question',
      name: q.question,
      acceptedAnswer: { '@type': 'Answer', text: q.answer },
    }))
    if (page.article) graph.push({ '@type': 'FAQPage', '@id': `${url}#domande`, mainEntity: entities })
    else webpage.mainEntity = entities
  }

  if (page.article) {
    graph.push({
      '@type': 'BlogPosting',
      '@id': `${url}#articolo`,
      headline: page.headline,
      description: page.description,
      datePublished: page.date,
      dateModified: page.updated || page.date,
      inLanguage: 'it-IT',
      articleSection: page.category,
      wordCount: page.words,
      image,
      author: { '@type': 'Organization', name: 'Redazione DottorCloud', url: `${origin}/approfondimenti/` },
      publisher: { '@id': org['@id'] },
      mainEntityOfPage: { '@id': `${url}#pagina` },
      isPartOf: { '@id': website['@id'] },
    })
  }

  const glossary = terms(html)
  if (glossary.length) {
    graph.push({
      '@type': 'DefinedTermSet',
      '@id': `${url}#glossario`,
      name: shortTitle(page.title),
      hasDefinedTerm: glossary.map((term) => ({
        '@type': 'DefinedTerm',
        '@id': `${url}#${term.id}`,
        name: term.name,
        description: term.description,
        inDefinedTermSet: `${url}#glossario`,
      })),
    })
  }

  const json = JSON.stringify({ '@context': 'https://schema.org', '@graph': graph })
  // a "</script>" inside a string would close the tag
  return `<script type="application/ld+json">${json.replace(/</g, '\\u003c')}</script>`
}

export function sitemap(origin, pages) {
  return (
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    pages
      .map(
        (page) =>
          `  <url><loc>${origin}${page.path}</loc>${page.lastmod ? `<lastmod>${page.lastmod}</lastmod>` : ''}</url>\n`,
      )
      .join('') +
    '</urlset>\n'
  )
}

const xml = (text) =>
  text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** The articles as an RSS feed, newest first. */
export function feed(origin, articles) {
  const items = articles
    .map(
      (a) => `    <item>
      <title>${xml(a.headline)}</title>
      <link>${origin}${a.path}</link>
      <guid isPermaLink="true">${origin}${a.path}</guid>
      <pubDate>${rssDate(a.date)}</pubDate>
      <category>${xml(a.category)}</category>
      <description>${xml(a.description)}</description>
    </item>\n`,
    )
    .join('')
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Approfondimenti · DottorCloud</title>
    <link>${origin}/approfondimenti/</link>
    <atom:link href="${origin}/approfondimenti/feed.xml" rel="self" type="application/rss+xml" />
    <description>Guide, norme e organizzazione per chi gestisce un centro medico.</description>
    <language>it-IT</language>
${items}  </channel>
</rss>
`
}
