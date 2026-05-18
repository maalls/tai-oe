import { afterEach, describe, expect, it, vi } from 'vitest';

import { getFamily } from '../../../../../src/api/family';

describe('getFamily', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns a family for a given id', async () => {
      const payload = {
         id: 'f1',
         name: 'Family A',
         brand_id: 'b1',
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getFamily('f1');

      expect(fetchMock).toHaveBeenCalledWith('/api/family/f1');
      expect(result).toEqual(payload);
   });

   it('throws when family is not found', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getFamily('missing')).rejects.toThrow('Famille introuvable');
   });
});
