import { afterEach, describe, expect, it, vi } from 'vitest';

import { getContact } from '../../../../../src/api/contact';

describe('getContact', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns the contact for a given id', async () => {
      const payload = {
         id: 'c1',
         account_id: 'a1',
         name: 'Alice',
         created_at: '2026-01-01',
         account_name: 'Acme',
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getContact('c1');

      expect(fetchMock).toHaveBeenCalledWith('/api/contact/c1');
      expect(result).toEqual(payload);
   });

   it('throws when contact is not found', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getContact('missing')).rejects.toThrow('Contact introuvable');
   });
});
