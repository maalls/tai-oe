import { afterEach, describe, expect, it, vi } from 'vitest';

import { listContacts } from '../../../../../src/api/contact';

describe('listContacts', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns contacts when API responds with ok', async () => {
      const payload = [{ id: 'c1', account_id: 'a1', name: 'Alice', created_at: '2026-01-01' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listContacts();

      expect(fetchMock).toHaveBeenCalledWith('/api/contact');
      expect(result).toEqual(payload);
   });

   it('throws when API responds with non-ok status', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(listContacts()).rejects.toThrow('Erreur lors du chargement des contacts');
   });
});
