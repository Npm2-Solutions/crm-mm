// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Whom the dialog opening a person's area starts on.
import { expect, test } from 'vitest'
import { chiEntraPerPrimo } from '@/utils/areaCliente'

test('the person, with an email of their own and nothing open yet', () => {
  expect(chiEntraPerPrimo({ email: 'anna@example.com' })).toBe('Self')
})

test('a child without an email: a parent or guardian', () => {
  expect(chiEntraPerPrimo({ email: '' })).toBe('Parent or guardian')
  expect(chiEntraPerPrimo({ email: null })).toBe('Parent or guardian')
  expect(chiEntraPerPrimo()).toBe('Parent or guardian')
})

test('their own access open: somebody else', () => {
  expect(
    chiEntraPerPrimo({ propriaAperta: true, email: 'anna@example.com' }),
  ).toBe('Parent or guardian')
})
