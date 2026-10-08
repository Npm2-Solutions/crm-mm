// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What a template's use allows, in the builder, and the forms on the centre's
 * website (crm/moduli/modelli.py `problemi_dell_uso`, crm/moduli/sito.py): the
 * same rules as the server, live; the address from a title; the code that puts a
 * form in another site. Pure: tested.
 */

import { fieldsOf } from './moduli'

/** The person's fields that find them again: a form on the website asks one. */
export const CONTACTS = ['email', 'mobile_no']

/**
 * What the use does not allow, as the server says it, for the builder's list of
 * things to fix: `{ field, message, args }`. ``forThePerson``: filled by the
 * person, who gives consents (a sheet is the operator's). ``onTheSite``: filled by
 * anybody on the website. ``personFields``: `[{ value, label }]`.
 */
export function useProblems(
  schema,
  {
    forThePerson = true,
    onTheSite = false,
    withoutCode = false,
    personFields = [],
  } = {},
) {
  const problems = []
  const fields = fieldsOf(schema)
  const known = new Map(personFields.map((f) => [f.value, f.label]))
  for (const [index, field] of fields.entries()) {
    // a question without words (a signature) by its place, never its key
    const label = field.label || __('Question {0}', [index + 1])
    // a survey opens with its link alone: nobody checked who holds it
    if (
      withoutCode &&
      ['consent', 'signature', 'attachment'].includes(field.type)
    ) {
      problems.push({
        field: field.id,
        message:
          '{0}: a survey opens with its link alone, so it asks no consent, signature or file',
        args: [label],
      })
      continue
    }
    if (field.type === 'consent' && !forThePerson) {
      problems.push({
        field: field.id,
        message:
          '{0}: a consent is given by the person, on a form. A sheet does not record it.',
        args: [label],
      })
    }
    if (!onTheSite) continue
    if (field.type === 'signature') {
      problems.push({
        field: field.id,
        message: '{0}: a form on the website is not signed',
        args: [label],
      })
    }
    if (field.type === 'attachment') {
      problems.push({
        field: field.id,
        message: '{0}: no file is sent from the website',
        args: [label],
      })
    }
    if (field.person && !known.has(field.person)) {
      problems.push({
        field: field.id,
        message: '{0}: the person has no field {1}',
        args: [label, field.person],
      })
    } else if (field.person && field.type !== 'text') {
      problems.push({
        field: field.id,
        message: "{0}: only a text question fills one of the person's fields",
        args: [label],
      })
    }
  }
  if (!onTheSite) return problems
  const filled = fields.map((f) => f.person).filter(Boolean)
  for (const key of new Set(filled)) {
    if (filled.filter((k) => k === key).length > 1) {
      problems.push({
        field: null,
        message: 'Two questions fill the same field of the person: {0}',
        args: [known.get(key) || key],
      })
    }
  }
  if (!CONTACTS.some((key) => filled.includes(key))) {
    problems.push({
      field: null,
      message:
        'A form on the website needs a question for the email or the mobile, to find the person again',
      args: [],
    })
  }
  return problems
}

/** An address from a title, as the server makes one: "Richiedi informazioni" is richiedi-informazioni. */
export function addressFrom(title) {
  const address = (title || '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70)
    .replace(/-+$/g, '')
  return address.length >= 2 ? address : 'modulo'
}

/** What is typed in the address, while it is typed: lowercase letters, digits and dashes. */
export function tidyAddress(value) {
  return (value || '')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+/, '')
    .slice(0, 80)
}

/** An address the server takes (`INDIRIZZO` in crm_form_template.py). */
export const ADDRESS_RE = /^[a-z0-9][a-z0-9-]{1,79}$/

// the server's ALLOWED_EMBEDDING_DOMAIN_RE (crm/www/crm_form.py): a bare host,
// maybe a scheme and a port, maybe a leading "*."; anything else is dropped
export const EMBEDDING_DOMAIN_RE =
  /^(https?:\/\/)?(\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?(?::\d+)?$/

/** The sites the form may be embedded in, one a line, and the ones that are not sites. */
export function embeddingDomains(text) {
  const domains = (text || '').split(/\s+/).filter(Boolean)
  return {
    domains,
    invalid: domains.filter((domain) => !EMBEDDING_DOMAIN_RE.test(domain)),
  }
}

const attribute = (value) =>
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

/**
 * The code a site pastes to show the form: the page in a frame, and a few words
 * of script so the frame grows with the form (the page tells its height).
 */
export function embedSnippet(url, route, title) {
  const origin = new URL(url).origin
  const id = `crm-form-${route}`
  return (
    `<iframe id="${id}" src="${url}?embed=1" title="${attribute(title)}" width="100%" height="640" style="border:0;width:100%" loading="lazy"></iframe>\n` +
    `<script>addEventListener("message",function(e){if(e.origin==="${origin}"&&e.data&&e.data.route===${JSON.stringify(route)}&&e.data.crmFormHeight){var f=document.getElementById(${JSON.stringify(id)});if(f)f.style.height=e.data.crmFormHeight+"px"}})</script>`
  )
}
