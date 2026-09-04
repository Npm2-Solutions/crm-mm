import { onMounted, onUnmounted } from 'vue'

// The provider login runs in a popup so the CRM keeps its state: navigating the
// whole app to facebook.com or accounts.google.com and back reloads it, and a
// failure on the way had nowhere to be shown. The popup lands on
// /oauth_connected, which posts the outcome here and closes.

export function openOAuthPopup(url, name = 'crm-oauth') {
  const width = 620
  const height = 720
  const left = window.screenX + (window.outerWidth - width) / 2
  const top = window.screenY + (window.outerHeight - height) / 2
  const popup = window.open(
    url,
    name,
    `popup=1,width=${width},height=${height},left=${left},top=${top}`,
  )
  if (!popup) {
    // popup blocked: fall back to navigating, the landing page handles it
    window.location.href = url
    return false
  }
  popup.focus()
  return true
}

/**
 * Run `handler({ error })` when the popup of `provider` reports back.
 * Registers on mount and cleans up on unmount.
 */
export function onOAuthResult(provider, handler) {
  function listener(event) {
    if (event.origin !== window.location.origin) return
    const data = event.data
    if (data?.source !== 'crm-oauth' || data.provider !== provider) return
    handler({ error: data.error || '' })
  }
  onMounted(() => window.addEventListener('message', listener))
  onUnmounted(() => window.removeEventListener('message', listener))
}
