/**
 * Embedded Signup, run from the CRM itself.
 *
 * Meta will only open this flow from a page whose domain is registered with the
 * app — *Allowed domains for the JavaScript SDK* and *Valid OAuth redirect
 * URIs*. With one site per client that list could never be complete, so clients
 * are sent to the hub's `/whatsapp-connect` page, which is on the one domain
 * the app does know.
 *
 * The agency is the exception, and it is the case we hit every day: its CRM is
 * *on* the hub. Same domain, already registered — so there is nothing for the
 * extra page to accomplish, and the button can open Facebook itself, the way
 * Meta's own builder does.
 */

const SDK_ID = 'facebook-jssdk'
const SDK_SRC = 'https://connect.facebook.net/en_US/sdk.js'
const GRAPH_VERSION = 'v23.0'

/** Would the hub page land on the domain we are already on? */
export function runsHere(hubOrigin, here) {
  if (!hubOrigin || !here) return false
  return (
    String(hubOrigin).replace(/\/+$/, '') === String(here).replace(/\/+$/, '')
  )
}

/**
 * Facebook's script, loaded once.
 *
 * Called early rather than on the click: `FB.login` opens a window, and a
 * browser only allows that from a gesture it is still handling. Waiting for a
 * script inside the handler loses the gesture, and the window is blocked.
 */
export function loadFacebookSdk(appId) {
  if (typeof window === 'undefined')
    return Promise.reject(new Error('no window'))
  if (window.FB) return Promise.resolve(window.FB)
  if (!window.__waSdkPromise) {
    window.__waSdkPromise = new Promise((resolve, reject) => {
      window.fbAsyncInit = function () {
        window.FB.init({
          appId,
          cookie: true,
          xfbml: false,
          version: GRAPH_VERSION,
        })
        resolve(window.FB)
      }
      const existing = document.getElementById(SDK_ID)
      if (existing) return
      const script = document.createElement('script')
      script.id = SDK_ID
      script.src = SDK_SRC
      script.async = true
      script.onerror = () => {
        window.__waSdkPromise = null
        reject(new Error('blocked'))
      }
      document.body.appendChild(script)
    })
  }
  return window.__waSdkPromise
}

/**
 * What Meta documents for Embedded Signup v4, plus the two things it does not.
 *
 * `extras` is where Coexistence is asked for: without `featureType` the flow
 * offers the plain Cloud API onboarding, which cannot take a number that is
 * already live on somebody's phone. `auth_type` counters Facebook skipping
 * every screen it already has an answer for, Coexistence among them, so a flow
 * that worked once would work differently the second time.
 *
 * `fallbackRedirectUri` is not optional, whatever its name suggests. From the
 * SDK's own source:
 *
 *     e.fallback_redirect_uri || (e.fallback_redirect_uri = document.location.href)
 *
 * Leave it out and the SDK fills it with **the page you are on**, and Facebook
 * checks that against the app's Valid OAuth Redirect URIs before it shows
 * anything. The CRM's own address is not in that list and has no business being
 * there, so what opens is a window saying the redirect is not allowed. Passing
 * the hub's connect page — which is in the list, and which already knows how to
 * finish a flow that comes back by redirect — is what stops that window from
 * ever opening.
 */
export function loginOptions(configId, fallbackRedirectUri) {
  return {
    config_id: configId,
    response_type: 'code',
    override_default_response_type: true,
    auth_type: 'reauthorize',
    fallback_redirect_uri: fallbackRedirectUri,
    extras: {
      setup: {},
      featureType: 'whatsapp_business_app_onboarding',
      sessionInfoVersion: '3',
    },
  }
}

/** The ids Embedded Signup reports over `postMessage`, as they arrive. */
export function listenForSignup(onEvent) {
  const handler = (event) => {
    if (!String(event.origin || '').endsWith('facebook.com')) return
    let data
    try {
      data = JSON.parse(event.data)
    } catch (e) {
      return
    }
    if (data.type !== 'WA_EMBEDDED_SIGNUP') return
    onEvent(data.event || 'STEP', data.data || {})
  }
  window.addEventListener('message', handler)
  return () => window.removeEventListener('message', handler)
}
