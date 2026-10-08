// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { createResource } from 'frappe-ui'

/**
 * A call asked once, here and now: its answer goes to `onSuccess`, a refusal to
 * `onError`, which says it in words. frappe-ui's resource throws again what it
 * handed to `onError`, and a resource made with `auto: true` is awaited by
 * nobody: a refusal the page had already told left an uncaught rejection over it.
 */
export function chiedi(options) {
  const risorsa = createResource({ ...options, auto: false })
  risorsa.fetch().catch(() => {})
  return risorsa
}
