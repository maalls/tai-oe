import { afterEach, describe, expect, it, vi } from 'vitest';

import { createContact } from '../../../../../src/api/contact';

describe('createContact', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts the payload and returns created contact', async () => {
      const payload = {
         id: 'c1',
         account_id: 'a1',
         name: 'Alice',
         email: 'alice@example.com',
         created_at: '2026-01-01',
      };
      const data = {
         account_id: 'a1',
         name: 'Alice',
         email: 'alice@example.com',
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createContact(data);

      expect(fetchMock).toHaveBeenCalledWith('/api/contact', {
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

      await expect(createContact({ account_id: 'a1', name: 'Alice' })).rejects.toThrow(
         'Erreur lors de la création du contact'
      );
   });
});
