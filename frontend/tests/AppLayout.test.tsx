import { describe, expect, it } from 'vitest'
import { initials } from '../src/layout/AppLayout'

describe('initials', () => {
  it('usa las dos primeras partes del nombre del email', () => {
    expect(initials('maria.silva@fazenda.com')).toBe('MS')
    expect(initials('produtor@test.com')).toBe('PR')
    expect(initials('a@b.com')).toBe('A')
  })
})
