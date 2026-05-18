import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateBrand } from '../../../../../src/api/brand';

describe('updateBrand', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts payload and returns updated brand', async () => {
      const payload = {
         id: 'b1',
         name: 'Brand A',
         vendor_id: 'v1',
         created_at: '2026-01-01',
         updated_at: '2026-01-01',
      };
      const data = { name: 'Brand A', vendor_id: 'v1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateBrand('b1', data);

      expect(fetchMock).toHaveBeenCalledWith('/api/brand/b1', {
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

      await expect(updateBrand('b1', { name: 'Brand A' })).rejects.toThrow(
         'Erreur lors de la mise à jour de la marque'
      );
   });
});
