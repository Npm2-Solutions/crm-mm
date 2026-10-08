import { describe, expect, it } from 'vitest'
import {
  ADDRESS_RE,
  addressFrom,
  embedSnippet,
  embeddingDomains,
  tidyAddress,
  useProblems,
} from '@/utils/moduliSito'

const PERSON = [
  { value: 'full_name', label: 'Name and surname' },
  { value: 'email', label: 'Email' },
  { value: 'mobile_no', label: 'Mobile' },
]

const form = (fields) => ({ sections: [{ id: 's', fields }] })
const codes = (problems) => problems.map((p) => p.message)

describe('what a use allows', () => {
  const contact = [
    { id: 'nome', type: 'text', label: 'Nome', person: 'full_name' },
    { id: 'email', type: 'text', label: 'Email', person: 'email' },
  ]

  it('a form of the website finds the person, and is neither signed nor sent files', () => {
    const site = { onTheSite: true, personFields: PERSON }
    expect(useProblems(form(contact), site)).toEqual([])
    const wrong = useProblems(
      form([
        { id: 'firma', type: 'signature', label: 'Firma' },
        { id: 'foto', type: 'attachment', label: 'Foto' },
        { id: 'eta', type: 'number', label: 'Età', person: 'full_name' },
        { id: 'nome', type: 'text', label: 'Nome', person: 'full_name' },
        { id: 'codice', type: 'text', label: 'Codice', person: 'tax_id' },
      ]),
      site,
    )
    expect(codes(wrong)).toEqual([
      '{0}: a form on the website is not signed',
      '{0}: no file is sent from the website',
      "{0}: only a text question fills one of the person's fields",
      '{0}: the person has no field {1}',
      'Two questions fill the same field of the person: {0}',
      'A form on the website needs a question for the email or the mobile, to find the person again',
    ])
    // the field's label, for the list of things to fix
    expect(wrong[4].args).toEqual(['Name and surname'])
    expect(wrong[0].field).toBe('firma')
  })

  it('a survey opens with its link alone: no consent, signature or file', () => {
    const survey = { withoutCode: true }
    const wrong = useProblems(
      form([
        { id: 'voto', type: 'scale', label: 'Voto', min: 0, max: 10 },
        { id: 'ok', type: 'consent', label: 'Privacy' },
        { id: 'firma', type: 'signature', label: 'Firma' },
        { id: 'foto', type: 'attachment', label: 'Foto' },
      ]),
      survey,
    )
    expect(wrong.map((p) => p.field)).toEqual(['ok', 'firma', 'foto'])
    expect(new Set(codes(wrong))).toEqual(
      new Set([
        '{0}: a survey opens with its link alone, so it asks no consent, signature or file',
      ]),
    )
  })

  it('a sheet records no consent; a form of the desk says nothing of the person', () => {
    const consent = { id: 'ok', type: 'consent', label: 'Privacy' }
    expect(
      codes(useProblems(form([consent]), { forThePerson: false })),
    ).toEqual([
      '{0}: a consent is given by the person, on a form. A sheet does not record it.',
    ])
    expect(useProblems(form([consent, ...contact]))).toEqual([])
    expect(
      useProblems(form([{ id: 'x', type: 'text', person: 'email' }])),
    ).toEqual([])
  })
})

describe('the address', () => {
  it('comes from the title as the server makes it', () => {
    expect(addressFrom('Richiedi informazioni')).toBe('richiedi-informazioni')
    expect(addressFrom('  Perché noi? Più è meglio!  ')).toBe(
      'perche-noi-piu-e-meglio',
    )
    expect(addressFrom('x')).toBe('modulo')
    expect(addressFrom('')).toBe('modulo')
    expect(addressFrom('a'.repeat(90))).toHaveLength(70)
  })

  it('takes lowercase letters, digits and dashes while it is typed', () => {
    expect(tidyAddress('Contatti_Sito')).toBe('contatti-sito')
    expect(tidyAddress('-promo ')).toBe('promo-')
    expect(ADDRESS_RE.test('contatti-sito')).toBe(true)
    expect(ADDRESS_RE.test('-contatti')).toBe(false)
    expect(ADDRESS_RE.test('c')).toBe(false)
  })
})

describe('in another site', () => {
  it('lists the sites that are not sites', () => {
    expect(
      embeddingDomains('https://www.example.com\n*.example.it\nbad;domain'),
    ).toEqual({
      domains: ['https://www.example.com', '*.example.it', 'bad;domain'],
      invalid: ['bad;domain'],
    })
    expect(embeddingDomains('')).toEqual({ domains: [], invalid: [] })
  })

  it('embeds the page, which grows with the form', () => {
    const snippet = embedSnippet(
      'https://centro.example.com/crm-form/contatti',
      'contatti',
      'Scrivici "ora"',
    )
    expect(snippet).toContain(
      'src="https://centro.example.com/crm-form/contatti?embed=1"',
    )
    expect(snippet).toContain('title="Scrivici &quot;ora&quot;"')
    expect(snippet).toContain('e.origin==="https://centro.example.com"')
    expect(snippet).toContain('e.data.route==="contatti"')
    expect(snippet).toContain('id="crm-form-contatti"')
  })
})
