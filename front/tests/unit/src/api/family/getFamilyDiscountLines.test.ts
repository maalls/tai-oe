import { afterEach, describe, expect, it, vi } from 'vitest';

import { getFamilyDiscountLines } from '../../../../../src/api/family';

describe('getFamilyDiscountLines', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns document id and lines for family discount', async () => {
      const payload = {
         document_id: 'd1',
         lines: [{ id: 'l1', position: 1 }],
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getFamilyDiscountLines('f1');

      expect(fetchMock).toHaveBeenCalledWith('/api/family/f1/discount-lines');
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getFamilyDiscountLines('f1')).rejects.toThrow(
         'Erreur lors du chargement des lignes de remise'
      );
   });
});
