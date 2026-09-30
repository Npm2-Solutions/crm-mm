import { describe, expect, it } from 'vitest'
import {
  RITMO,
  TEMPO,
  aCheTappa,
  nuovaTappa,
  perIlServer,
} from '@/utils/programmi'

describe('a programme in the editor', () => {
  it('starts a stage with its own key and nothing else', () => {
    const tappa = nuovaTappa('Prima', () => 0.5)
    expect(tappa).toEqual({
      key: '88888888',
      title: 'Prima',
      description: '',
      days: '',
      plan: null,
    })
  })

  it('sends the words and the order, the days only by time', () => {
    const bozza = {
      title: 'Percorso',
      mode: TEMPO,
      starts_on: '2026-10-05',
      stages: [
        { key: 'a', title: 'Uno', days: '7', state: 'open', plan: 'p1' },
        { key: 'b', title: 'Due', days: '', description: 'Poi' },
      ],
    }
    expect(perIlServer(bozza)).toEqual({
      title: 'Percorso',
      mode: TEMPO,
      starts_on: '2026-10-05',
      instructions: null,
      stages: [
        { key: 'a', title: 'Uno', description: null, days: 7, plan: 'p1' },
        { key: 'b', title: 'Due', description: 'Poi', days: null, plan: null },
      ],
    })
    expect(perIlServer({ ...bozza, mode: RITMO }).stages[0].days).toBeNull()
  })

  it('says how far the patient is', () => {
    const stati = (...s) => ({ stages: s.map((state) => ({ state })) })
    expect(aCheTappa(stati('done', 'open', 'locked'))).toBe('Stage 2 of 3')
    expect(aCheTappa(stati('done', 'done'))).toBe('All stages done')
    expect(aCheTappa(stati('locked', 'locked'))).toBe('Not started yet')
  })
})
