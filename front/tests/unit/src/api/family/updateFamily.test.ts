import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateFamily } from '../../../../../src/api/family';

describe('updateFamily', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts payload and returns updated family', async () => {
      const payload = {
         id: 'f1',
         name: 'Family A',
         brand_id: 'b1',
      };
      const data = { name: 'Family A', product_code: 'SKU-1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateFamily('f1', data);

      expect(fetchMock).toHaveBeenCalledWith('/api/family/f1', {
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

      await expect(updateFamily('f1', { name: 'Family A' })).rejects.toThrow(
         'Erreur lors de la mise à jour de la famille'
      );
   });
});
