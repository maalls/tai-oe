import { afterEach, describe, expect, it, vi } from 'vitest';

import { getBrand } from '../../../../../src/api/brand';

describe('getBrand', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns the brand for a given id', async () => {
      const payload = {
         id: 'b1',
         name: 'Brand A',
         vendor_id: 'v1',
         created_at: '2026-01-01',
         updated_at: '2026-01-01',
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getBrand('b1');

      expect(fetchMock).toHaveBeenCalledWith('/api/brand/b1');
      expect(result).toEqual(payload);
   });

   it('throws when brand is not found', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getBrand('missing')).rejects.toThrow('Marque introuvable');
   });
});
