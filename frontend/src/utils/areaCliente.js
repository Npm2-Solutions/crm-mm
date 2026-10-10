// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Whom the dialog that opens a person's client area starts on (`Area/AreaAccessCard`):
 * the person, while their own access is closed and they have an email of their
 * own; else a parent or guardian - a child with no email is entered by who
 * answers for them, and once the person's own access is open what is left is
 * letting somebody else in.
 */
export function chiEntraPerPrimo({ propriaAperta = false, email = '' } = {}) {
  return propriaAperta || !email ? 'Parent or guardian' : 'Self'
}
