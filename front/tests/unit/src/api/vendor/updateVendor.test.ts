import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateVendor } from '../../../../../src/api/vendor';

describe('updateVendor', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('updates vendor and returns API payload', async () => {
      const payload = {
         id: 'v1',
         name: 'ACME Updated',
         created_at: '2026-01-01',
         updated_at: '2026-01-02',
      };
      const data = { name: 'ACME Updated' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateVendor('v1', data);

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor/v1', {
         method: 'PUT',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(data),
      });
      expect(result).toEqual(payload);
   });

   it('throws when update fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(updateVendor('v1', { name: 'ACME' })).rejects.toThrow(
         'Erreur lors de la mise à jour du fournisseur'
      );
   });
});
