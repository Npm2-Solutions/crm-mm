// Programmes of stages in the editor: the same ways as
// crm/clinica/programmi_regole.py, and what a draft sends to the server.
import { nuovaChiave } from '@/utils/piani'

export const TEMPO = 'By time'
export const RITMO = 'At own pace'

export function nuovaTappa(title = '', random) {
  return {
    key: nuovaChiave(random),
    title,
    description: '',
    days: '',
    plan: null,
  }
}

// a draft as the server keeps it: the words and the order, never the states
export function perIlServer(programma) {
  return {
    title: programma.title || '',
    mode: programma.mode || RITMO,
    starts_on: programma.starts_on || null,
    instructions: programma.instructions || null,
    stages: (programma.stages || []).map((tappa) => ({
      key: tappa.key,
      title: tappa.title || '',
      description: tappa.description || null,
      days:
        programma.mode === TEMPO && Number(tappa.days) > 0
          ? Number(tappa.days)
          : null,
      plan: tappa.plan || null,
    })),
  }
}

// how far the patient is: "stage 2 of 5", or where it stands when none is open
export function aCheTappa(programma, t = (s, a) => format(s, a)) {
  const tappe = programma?.stages || []
  const aperta = tappe.findIndex((tappa) => tappa.state === 'open')
  if (aperta >= 0) return t('Stage {0} of {1}', [aperta + 1, tappe.length])
  if (tappe.length && tappe.every((tappa) => tappa.state === 'done'))
    return t('All stages done')
  return t('Not started yet')
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}
