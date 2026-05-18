import { afterEach, describe, expect, it, vi } from 'vitest';

import { deleteContact } from '../../../../../src/api/contact';

describe('deleteContact', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('deletes the contact and returns deleted id', async () => {
      const payload = { id: 'c1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await deleteContact('c1');

      expect(fetchMock).toHaveBeenCalledWith('/api/contact/c1', { method: 'DELETE' });
      expect(result).toEqual(payload);
   });

   it('throws when deletion fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(deleteContact('c1')).rejects.toThrow('Erreur lors de la suppression du contact');
   });
});
