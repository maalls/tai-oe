import { afterEach, describe, expect, it, vi } from 'vitest';

import { createBrand } from '../../../../../src/api/brand';

describe('createBrand', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created brand', async () => {
      const payload = {
         id: 'b1',
         name: 'Brand A',
         vendor_id: 'v1',
         created_at: '2026-01-01',
         updated_at: '2026-01-01',
      };
      const data = { name: 'Brand A', vendor_id: 'v1', minimum_margin: 10 };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createBrand(data);

      expect(fetchMock).toHaveBeenCalledWith('/api/brand', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(data),
      });
      expect(result).toEqual(payload);
   });

   it('throws when creation fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(createBrand({ name: 'Brand A', vendor_id: 'v1' })).rejects.toThrow(
         'Erreur lors de la création de la marque'
      );
   });
});
