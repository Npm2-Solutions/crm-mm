// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The site's few behaviours: the menu on a phone, the header's line once the
// page scrolls, things arriving as they come into view, the video's play
// button, the chapters of the features page and the demo form sent without
// leaving the page. Every page works without it.

const header = document.querySelector('.site-header')

// the menu on a phone: without the script the button leads to the footer's links
const toggle = document.querySelector('.nav-toggle')
if (header && toggle) {
  toggle.setAttribute('role', 'button')
  const setOpen = (open) => {
    toggle.setAttribute('aria-expanded', String(open))
    header.classList.toggle('is-open', open)
  }
  toggle.addEventListener('click', (event) => {
    event.preventDefault()
    setOpen(toggle.getAttribute('aria-expanded') !== 'true')
  })
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && header.classList.contains('is-open')) {
      setOpen(false)
      toggle.focus()
    }
  })
  header
    .querySelectorAll('.nav a')
    .forEach((link) => link.addEventListener('click', () => setOpen(false)))
}

// a line under the header once the page has moved
if (header) {
  const onScroll = () =>
    header.classList.toggle('is-scrolled', window.scrollY > 8)
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
}

// things arriving as they come into view
const arriving = document.querySelectorAll('.reveal')
const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches
if (arriving.length && 'IntersectionObserver' in window && !still) {
  const seen = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        entry.target.classList.add('is-visible')
        seen.unobserve(entry.target)
      }
    },
    { rootMargin: '0px 0px -8% 0px' },
  )
  arriving.forEach((element) => seen.observe(element))
  document.documentElement.classList.add('reveal-on')
}

// the video starts from its own button, then has the browser's controls
document.querySelectorAll('[data-video]').forEach((frame) => {
  const video = frame.querySelector('video')
  const play = frame.querySelector('.video__play')
  if (!video || !play) return
  video.removeAttribute('controls')
  play.hidden = false
  play.addEventListener('click', () => {
    play.hidden = true
    video.controls = true
    video.play().catch(() => {})
    video.focus()
  })
})

// the chapter being read, lit in the bar of the features page
const chapterLinks = [...document.querySelectorAll('.chapters a[href^="#"]')]
if (chapterLinks.length && 'IntersectionObserver' in window) {
  const byId = new Map(
    chapterLinks.map((link) => [link.getAttribute('href').slice(1), link]),
  )
  const bar = document.querySelector('.chapters ol')
  const reading = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        const link = byId.get(entry.target.id)
        for (const other of chapterLinks) {
          if (other === link) other.setAttribute('aria-current', 'true')
          else other.removeAttribute('aria-current')
        }
        // on a phone the bar scrolls sideways: keep the lit chapter in it
        if (link && bar && bar.scrollWidth > bar.clientWidth) {
          bar.scrollTo({
            left: link.offsetLeft - 16,
            behavior: still ? 'auto' : 'smooth',
          })
        }
      }
    },
    { rootMargin: '-45% 0px -50% 0px' },
  )
  byId.forEach((_, id) => {
    const chapter = document.getElementById(id)
    if (chapter) reading.observe(chapter)
  })
}

// the demo form: the same address as without JavaScript, the answer in place
const form = document.querySelector('form[data-demo]')
if (form) {
  // how long the form was open, for the server's check against machines
  const openedAt = Date.now()
  const elapsed = form.querySelector('input[name="t"]')
  const status = form.querySelector('.form__status')
  const submit = form.querySelector('button[type="submit"]')
  const done = document.querySelector('[data-demo-sent]')

  const showErrors = (errors) => {
    let first = null
    form.querySelectorAll('[data-error-for]').forEach((slot) => {
      const name = slot.getAttribute('data-error-for')
      const field = form.elements.namedItem(name)
      const message = errors[name] || ''
      slot.textContent = message
      if (field && 'setAttribute' in field) {
        if (message) field.setAttribute('aria-invalid', 'true')
        else field.removeAttribute('aria-invalid')
      }
      if (message && !first) first = field
    })
    if (first && 'focus' in first) first.focus()
  }

  form.addEventListener('input', (event) => {
    const field = event.target
    if (field.getAttribute('aria-invalid') !== 'true') return
    field.removeAttribute('aria-invalid')
    const slot = form.querySelector(`[data-error-for="${field.name}"]`)
    if (slot) slot.textContent = ''
  })

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    if (elapsed) elapsed.value = String(Date.now() - openedAt)
    status.textContent = ''
    status.className = 'form__status'
    submit.setAttribute('aria-busy', 'true')
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      })
      const answer = await response.json().catch(() => ({}))
      if (response.ok && answer.ok) {
        form.hidden = true
        if (done) {
          done.hidden = false
          done.querySelector('h2')?.focus()
        }
        return
      }
      if (answer.errori) showErrors(answer.errori)
      status.classList.add('form__status--error')
      status.textContent =
        answer.messaggio ||
        'Non siamo riusciti a inviare la richiesta. Riprova tra poco, o scrivici all’indirizzo in questa pagina.'
    } catch {
      status.classList.add('form__status--error')
      status.textContent =
        'Non siamo riusciti a raggiungere il sito. Controlla la connessione, o scrivici all’indirizzo in questa pagina.'
    } finally {
      submit.removeAttribute('aria-busy')
    }
  })
}
