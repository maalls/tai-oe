import { afterEach, describe, expect, it, vi } from 'vitest';

import { saveFamilyDiscountLines } from '../../../../../src/api/family';

describe('saveFamilyDiscountLines', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts lines payload and returns updated lines', async () => {
      const payload = {
         document_id: 'd1',
         lines: [{ id: 'l1', position: 1 }],
      };
      const data = [{ id: 'l1', position: 1 }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await saveFamilyDiscountLines('f1', data as any);

      expect(fetchMock).toHaveBeenCalledWith('/api/family/f1/discount-lines', {
         method: 'PUT',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ lines: data }),
      });
      expect(result).toEqual(payload);
   });

   it('throws when save fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(saveFamilyDiscountLines('f1', [])).rejects.toThrow(
         'Erreur lors de la sauvegarde des lignes de remise'
      );
   });
});
