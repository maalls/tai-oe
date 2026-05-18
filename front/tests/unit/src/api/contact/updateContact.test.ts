import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateContact } from '../../../../../src/api/contact';

describe('updateContact', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('updates the contact and returns the API payload', async () => {
      const payload = {
         id: 'c1',
         account_id: 'a1',
         name: 'Alice Updated',
         created_at: '2026-01-01',
      };
      const data = { name: 'Alice Updated' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateContact('c1', data);

      expect(fetchMock).toHaveBeenCalledWith('/api/contact/c1', {
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

      await expect(updateContact('c1', { name: 'Alice' })).rejects.toThrow(
         'Erreur lors de la mise à jour du contact'
      );
   });
});
