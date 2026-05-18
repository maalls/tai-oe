import { afterEach, describe, expect, it, vi } from 'vitest';

import { createFamily } from '../../../../../src/api/family';

describe('createFamily', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created family', async () => {
      const payload = {
         id: 'f1',
         name: 'Family A',
         brand_id: 'b1',
      };
      const data = { name: 'Family A', type: 'discount', brand_id: 'b1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createFamily(data);

      expect(fetchMock).toHaveBeenCalledWith('/api/family', {
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

      await expect(createFamily({ brand_id: 'b1', type: 'discount' })).rejects.toThrow(
         'Erreur lors de la création de la famille'
      );
   });
});
