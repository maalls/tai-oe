import { afterEach, describe, expect, it, vi } from 'vitest';

import { listVendors } from '../../../../../src/api/vendor';

describe('listVendors', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns vendors when API responds with ok', async () => {
      const payload = [
         { id: 'v1', name: 'ACME', created_at: '2026-01-01', updated_at: '2026-01-01' },
      ];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listVendors();

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor');
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

      await expect(listVendors()).rejects.toThrow('Erreur lors du chargement des fournisseurs');
   });
});
