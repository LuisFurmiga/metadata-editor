import { describe, expect, it } from 'vitest';
import { stringify } from './format';

describe('stringify', () => {
  it('apresenta listas do ExifTool separadas por ponto e vírgula', () => {
    expect(stringify(['Caio Melo', 'curriculum vitæ', 'résumé'])).toBe(
      'Caio Melo; curriculum vitæ; résumé',
    );
  });

  it('mantém texto simples sem serialização JSON', () => {
    expect(stringify('Caio Melo')).toBe('Caio Melo');
  });
});
