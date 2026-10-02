// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// IndexNow: after a publish, tells Bing, Yandex, Seznam and Naver (and the
// AI answers that search through Bing) which pages changed, instead of waiting
// for their crawlers. The key is public by design: the site serves it at
// /<key>.txt to prove the request comes from its owner.
//
//   node sito/indexnow.mjs https://dottorcloud.com            the pages changed today
//   node sito/indexnow.mjs https://dottorcloud.com 2026-10-01 changed since that day

export const INDEXNOW_KEY = 'f9568769b55a1cfa3783654cb910d25d'

// the sitemap's addresses whose lastmod is on or after the day (YYYY-MM-DD)
export function changedSince(xml, day) {
  const urls = []
  for (const [, entry] of xml.matchAll(/<url>([\s\S]*?)<\/url>/g)) {
    const loc = entry.match(/<loc>([^<]+)<\/loc>/)?.[1]
    const lastmod = entry.match(/<lastmod>([^<]+)<\/lastmod>/)?.[1]
    if (loc && (!lastmod || lastmod.slice(0, 10) >= day)) urls.push(loc)
  }
  return urls
}

export function request(origin, urls) {
  return {
    host: new URL(origin).host,
    key: INDEXNOW_KEY,
    keyLocation: `${origin}/${INDEXNOW_KEY}.txt`,
    urlList: urls,
  }
}

async function main() {
  const origin = (process.argv[2] || 'https://dottorcloud.com').replace(/\/+$/, '')
  const day = process.argv[3] || new Date().toISOString().slice(0, 10)
  const xml = await (await fetch(`${origin}/sitemap.xml`)).text()
  const urls = changedSince(xml, day)
  if (!urls.length) {
    console.log(`IndexNow: nothing changed since ${day}.`)
    return
  }
  const answer = await fetch('https://api.indexnow.org/indexnow', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request(origin, urls)),
  })
  // 200 and 202 both mean received; anything else is reported, never fatal
  console.log(`IndexNow: ${urls.length} pages, answer ${answer.status}.`)
  for (const url of urls) console.log(`  ${url}`)
}

if (import.meta.url === `file://${process.argv[1]}`) await main()
