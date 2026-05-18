import { afterEach, describe, expect, it, vi } from 'vitest';

import { createVendor } from '../../../../../src/api/vendor';

describe('createVendor', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created vendor', async () => {
      const payload = {
         id: 'v1',
         name: 'ACME',
         created_at: '2026-01-01',
         updated_at: '2026-01-01',
      };
      const data = { name: 'ACME', email: 'hello@acme.com' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createVendor(data);

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor', {
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

      await expect(createVendor({ name: 'ACME' })).rejects.toThrow(
         'Erreur lors de la création du fournisseur'
      );
   });
});
