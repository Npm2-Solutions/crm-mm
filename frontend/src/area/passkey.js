// Passkeys in the browser: the server speaks JSON with base64url, the browser's
// WebAuthn API speaks ArrayBuffers. These convert one to the other, and ask the
// phone; the server checks everything (crm/clinica/area/passkey.py).

export function supported() {
  return (
    typeof window !== 'undefined' &&
    typeof window.PublicKeyCredential !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    Boolean(navigator.credentials)
  )
}

export function daBase64url(testo) {
  const base64 = testo.replace(/-/g, '+').replace(/_/g, '/')
  const pieno = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
  const binario = atob(pieno)
  const byte = new Uint8Array(binario.length)
  for (let i = 0; i < binario.length; i++) byte[i] = binario.charCodeAt(i)
  return byte.buffer
}

export function aBase64url(buffer) {
  const byte = new Uint8Array(buffer)
  let binario = ''
  for (const b of byte) binario += String.fromCharCode(b)
  return btoa(binario)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

const descrittori = (lista) =>
  (lista || []).map((d) => ({ ...d, id: daBase64url(d.id) }))

// the server's options, as navigator.credentials.create() wants them
export function opzioniDiCreazione(json) {
  return {
    ...json,
    challenge: daBase64url(json.challenge),
    user: { ...json.user, id: daBase64url(json.user.id) },
    excludeCredentials: descrittori(json.excludeCredentials),
  }
}

// the server's options, as navigator.credentials.get() wants them
export function opzioniDiAccesso(json) {
  return {
    ...json,
    challenge: daBase64url(json.challenge),
    allowCredentials: descrittori(json.allowCredentials),
  }
}

// what the phone answered, as the server reads it
export function inJSON(credenziale) {
  const r = credenziale.response
  const risposta = { clientDataJSON: aBase64url(r.clientDataJSON) }
  if (r.attestationObject) {
    risposta.attestationObject = aBase64url(r.attestationObject)
    if (typeof r.getTransports === 'function')
      risposta.transports = r.getTransports()
  }
  if (r.authenticatorData) {
    risposta.authenticatorData = aBase64url(r.authenticatorData)
    risposta.signature = aBase64url(r.signature)
    if (r.userHandle) risposta.userHandle = aBase64url(r.userHandle)
  }
  return {
    id: credenziale.id,
    rawId: aBase64url(credenziale.rawId),
    type: credenziale.type,
    response: risposta,
    clientExtensionResults:
      typeof credenziale.getClientExtensionResults === 'function'
        ? credenziale.getClientExtensionResults()
        : {},
    authenticatorAttachment: credenziale.authenticatorAttachment || undefined,
  }
}
