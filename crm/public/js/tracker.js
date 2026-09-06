/**
 * CRM lead tracker.
 *
 * Paste one tag on any website — yours or a customer's — and every visit is
 * recorded against a browser that the CRM can later recognise as a lead:
 *
 *   <script async src="https://crm.example.com/assets/crm/js/tracker.js"></script>
 *
 * What it does, in order of how much it matters:
 *
 *   1. Remembers the browser (`localStorage`, first-party on the site it runs on)
 *      and the current visit, and sends both back with everything it reports.
 *   2. Records page views — including SPA route changes — with the time spent.
 *   3. Carries the ids into anything that can create a lead: CRM forms embedded
 *      in an iframe, plain HTML forms on the page, tracked links.
 *   4. Records outbound, `tel:` and `mailto:` clicks, so "which link did they
 *      click" has an answer.
 *
 * Attribution itself — which campaign, which medium, paid or organic — is worked
 * out server-side from the landing URL and the referrer. The script's whole job
 * is to make sure the server sees them, and sees them attached to the right
 * browser.
 *
 * No dependencies, no cookies of its own on the visitor's site, nothing sent
 * before consent when the CRM is configured to require it.
 */
;(function (window, document) {
  'use strict'

  if (window.CRMTracker && window.CRMTracker.__loaded) return

  // ---------------------------------------------------------------------------
  // Configuration
  // ---------------------------------------------------------------------------

  var script = document.currentScript || (function () {
    var all = document.getElementsByTagName('script')
    for (var i = all.length - 1; i >= 0; i--) {
      if (all[i].src && all[i].src.indexOf('tracker.js') !== -1) return all[i]
    }
    return null
  })()

  // The CRM's own origin: told to us explicitly, or inferred from where this
  // file was served from — which is the same thing in every normal install.
  var BASE = (script && (script.getAttribute('data-crm') || script.src.split('/assets/')[0])) || ''
  BASE = BASE.replace(/\/+$/, '')
  if (!BASE) return

  var ENDPOINT = BASE + '/api/method/crm.api.tracking.collect'
  var STORAGE_VID = 'crm_vid'
  var STORAGE_SID = 'crm_sid'
  var STORAGE_SEEN = 'crm_last_seen'
  var STORAGE_CONSENT = 'crm_consent'
  var SESSION_TIMEOUT_MS = 30 * 60 * 1000

  var requireConsent = script && script.getAttribute('data-consent') === 'required'
  var doNotTrack =
    navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.msDoNotTrack === '1'

  // ---------------------------------------------------------------------------
  // Storage — every access guarded: Safari private mode throws on write
  // ---------------------------------------------------------------------------

  function read(key) {
    try {
      return window.localStorage.getItem(key)
    } catch (e) {
      return null
    }
  }

  function write(key, value) {
    try {
      window.localStorage.setItem(key, value)
    } catch (e) {
      /* private mode, or storage disabled — we simply forget between pages */
    }
  }

  // ---------------------------------------------------------------------------
  // Identity
  // ---------------------------------------------------------------------------

  /**
   * An id handed to us on the URL wins over whatever this site had stored.
   *
   * That is how a click from an email or SMS keeps its identity: the redirect
   * cannot write to this site's storage, so it appends `?crm_vid=…` and the
   * landing page adopts it. Everything read after the click then lands on the
   * lead that was emailed, instead of starting a fresh anonymous trail.
   */
  function idFromUrl(key) {
    var match = new RegExp('[?&]' + key + '=([0-9a-f]{32})').exec(location.search)
    return match ? match[1] : ''
  }

  var visitorId = idFromUrl('crm_vid') || read(STORAGE_VID) || ''
  var sessionId = idFromUrl('crm_sid') || read(STORAGE_SID) || ''
  if (idFromUrl('crm_vid')) write(STORAGE_VID, visitorId)

  // A visit that has been idle past the timeout is over; the server decides
  // definitively (it also starts a new session when the campaign changes), but
  // dropping the stale id here keeps the two in step.
  var lastSeen = parseInt(read(STORAGE_SEEN) || '0', 10)
  if (lastSeen && Date.now() - lastSeen > SESSION_TIMEOUT_MS) sessionId = ''

  function remember(ids) {
    var changed = false
    if (ids.vid && ids.vid !== visitorId) {
      visitorId = ids.vid
      write(STORAGE_VID, visitorId)
      changed = true
    }
    if (ids.sid && ids.sid !== sessionId) {
      sessionId = ids.sid
      write(STORAGE_SID, sessionId)
      changed = true
    }
    write(STORAGE_SEEN, String(Date.now()))

    // On a brand-new browser there is no id until the first beacon comes back.
    // The forms were already scanned by then and carry a blank one, so re-stamp
    // them — otherwise the very first submission of a first-ever visit, which is
    // exactly the one worth attributing, arrives anonymous.
    if (changed && started) stampForms()
  }

  function hasConsent() {
    return !requireConsent || read(STORAGE_CONSENT) === '1'
  }

  function enabled() {
    return !doNotTrack && hasConsent()
  }

  // ---------------------------------------------------------------------------
  // Transport
  // ---------------------------------------------------------------------------

  var started = false
  var queue = []
  var flushTimer = null

  function enqueue(event) {
    if (!enabled()) return
    queue.push(event)
    if (flushTimer) clearTimeout(flushTimer)
    // batch the burst a page load produces into one request, but never sit on
    // an event long enough to lose it to a navigation
    flushTimer = setTimeout(flush, 300)
  }

  function payload(events) {
    return JSON.stringify({
      vid: visitorId || null,
      sid: sessionId || null,
      consent: hasConsent(),
      client: {
        lang: navigator.language || '',
        screen: (window.screen && window.screen.width + 'x' + window.screen.height) || '',
      },
      events: events,
    })
  }

  function flush(useBeacon) {
    if (flushTimer) {
      clearTimeout(flushTimer)
      flushTimer = null
    }
    if (!queue.length || !enabled()) return
    var events = queue.splice(0, queue.length)
    var body = payload(events)

    // `text/plain` keeps this a "simple" request: no CORS preflight, so a page
    // view costs one round trip instead of two and works on a site whose origin
    // the CRM has not been told about yet.
    if (useBeacon && navigator.sendBeacon) {
      try {
        navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'text/plain;charset=UTF-8' }))
        return
      } catch (e) {
        /* fall through to fetch */
      }
    }

    try {
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        body: body,
        credentials: 'include',
        keepalive: true,
      })
        .then(function (r) {
          return r.json()
        })
        .then(function (data) {
          if (data && data.message) remember(data.message)
        })
        .catch(function () {})
    } catch (e) {
      /* the page is going away; the beacon path above already covered us */
    }
  }

  // ---------------------------------------------------------------------------
  // Page views
  // ---------------------------------------------------------------------------

  var currentPath = null
  var enteredAt = Date.now()
  var firstView = true

  function trackPageView() {
    var path = location.pathname + location.search
    if (path === currentPath) return
    if (currentPath !== null) reportTimeOnPage()

    currentPath = path
    enteredAt = Date.now()
    enqueue({
      type: 'page_view',
      url: location.href,
      title: document.title || '',
      // only the real referrer counts as the referrer; within an SPA the
      // "referrer" is the page we just left
      referrer: firstView ? document.referrer || '' : location.origin + (currentPath || ''),
    })
    firstView = false
    scanForms()
  }

  function reportTimeOnPage() {
    var seconds = Math.round((Date.now() - enteredAt) / 1000)
    if (seconds < 1 || seconds > 60 * 60) return
    enqueue({ type: 'page_view', url: location.href, title: document.title || '', duration: seconds })
  }

  function watchHistory() {
    ;['pushState', 'replaceState'].forEach(function (method) {
      var original = history[method]
      if (typeof original !== 'function') return
      history[method] = function () {
        var result = original.apply(this, arguments)
        setTimeout(trackPageView, 0)
        return result
      }
    })
    window.addEventListener('popstate', function () {
      setTimeout(trackPageView, 0)
    })
  }

  // ---------------------------------------------------------------------------
  // Forms — the point where a visitor becomes a lead
  // ---------------------------------------------------------------------------

  var CRM_FORM_MARKER = '/crm-form/'
  var BOOKING_MARKER = '/book/'

  function scanForms() {
    scanIframes()
    scanNativeForms()
  }

  /** Refresh the ids already-scanned forms carry, without rescanning. */
  function stampForms() {
    scanIframes()
    var forms = document.getElementsByTagName('form')
    for (var i = 0; i < forms.length; i++) setIds(forms[i])
  }

  /**
   * A CRM form embedded in an iframe runs on the CRM's own origin, so it cannot
   * read this page's storage. Hand it the ids on its URL instead — the form page
   * forwards them with the submission.
   */
  function scanIframes() {
    if (!visitorId) return
    var frames = document.getElementsByTagName('iframe')
    for (var i = 0; i < frames.length; i++) {
      var frame = frames[i]
      var src = frame.getAttribute('src') || ''
      if (src.indexOf(CRM_FORM_MARKER) === -1 && src.indexOf(BOOKING_MARKER) === -1) continue
      if (src.indexOf('crm_vid=') !== -1) continue
      frame.setAttribute(
        'src',
        src +
          (src.indexOf('?') === -1 ? '?' : '&') +
          'crm_vid=' +
          encodeURIComponent(visitorId) +
          '&crm_sid=' +
          encodeURIComponent(sessionId || '')
      )
    }
  }

  /**
   * A form posted by the host site (its own backend, Webflow, WordPress, a
   * third-party handler) gets the ids as hidden inputs, so whatever eventually
   * reaches the CRM still carries them.
   */
  function scanNativeForms() {
    var forms = document.getElementsByTagName('form')
    for (var i = 0; i < forms.length; i++) {
      var form = forms[i]
      if (form.getAttribute('data-crm-tracked')) continue
      form.setAttribute('data-crm-tracked', '1')
      setIds(form)
      form.addEventListener('submit', onFormSubmit)
      enqueue({ type: 'form_view', url: location.href, label: formLabel(form) })
    }
  }

  function setIds(form) {
    setHidden(form, 'crm_vid', visitorId)
    setHidden(form, 'crm_sid', sessionId || '')
  }

  function setHidden(form, name, value) {
    var input = form.querySelector('input[name="' + name + '"]')
    if (!input) {
      input = document.createElement('input')
      input.type = 'hidden'
      input.name = name
      form.appendChild(input)
    }
    input.value = value
  }

  function formLabel(form) {
    return form.getAttribute('name') || form.getAttribute('id') || form.action || 'form'
  }

  function onFormSubmit(event) {
    var form = event.target
    setIds(form) // last chance: the ids may have arrived since the scan
    enqueue({ type: 'form_submit', url: location.href, label: formLabel(form) })
    flush(true)
  }

  // ---------------------------------------------------------------------------
  // Link clicks
  // ---------------------------------------------------------------------------

  function onClick(event) {
    var node = event.target
    while (node && node.nodeName !== 'A') node = node.parentNode
    if (!node || !node.href) return

    var href = node.href
    var outbound = node.hostname && node.hostname !== location.hostname
    var contact = href.indexOf('tel:') === 0 || href.indexOf('mailto:') === 0
    if (!outbound && !contact) return

    enqueue({
      type: 'link_click',
      url: href,
      label: (node.textContent || '').trim().slice(0, 140) || href,
      referrer: location.href,
    })
    flush(true)
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  var api = {
    __loaded: true,

    /** Record something the page cares about: `CRMTracker.track('video_watched', {id: 3})`. */
    track: function (name, props) {
      enqueue({ type: 'custom', name: String(name || 'event'), url: location.href, props: props || {} })
      flush()
    },

    /** Tell the CRM who this is, when the page already knows (a logged-in area). */
    identify: function (traits) {
      enqueue({ type: 'identify', url: location.href, props: traits || {} })
      flush()
    },

    /** Grant or withdraw consent from a cookie banner. */
    consent: function (granted) {
      write(STORAGE_CONSENT, granted ? '1' : '0')
      if (granted) {
        start()
      }
    },

    /** The ids, for a form your own code builds and posts. */
    getIds: function () {
      return { vid: visitorId, sid: sessionId }
    },

    /** Re-scan after injecting a form into the page. */
    refresh: scanForms,
  }

  // ---------------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------------

  function start() {
    if (started || !enabled()) return
    started = true

    trackPageView()
    watchHistory()
    document.addEventListener('click', onClick, true)

    // A form may be injected long after load (a modal, a lazy embed), so watch
    // for it rather than making the host site call refresh(). Coalesced: an SPA
    // re-rendering mutates constantly, and this runs on someone else's page.
    if (window.MutationObserver) {
      var rescan = null
      new MutationObserver(function () {
        if (rescan) return
        rescan = setTimeout(function () {
          rescan = null
          scanForms()
        }, 500)
      }).observe(document.documentElement, { childList: true, subtree: true })
    }

    window.addEventListener('pagehide', function () {
      reportTimeOnPage()
      flush(true)
    })
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') {
        reportTimeOnPage()
        flush(true)
      }
    })
  }

  window.CRMTracker = api

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start)
  } else {
    start()
  }
})(window, document)
