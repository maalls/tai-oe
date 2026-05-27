import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchAuthUser } from '../../../../../src/api/authUser';

describe('fetchAuthUser', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns payload when API responds with ok', async () => {
      const payload = { user: { id: 'u-1', role: 'admin' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await fetchAuthUser('token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/auth/user', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload);
   });

   it('throws backend message when API responds with non-ok status', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'Unauthorized' }),
         })
      );

      await expect(fetchAuthUser('token-1')).rejects.toThrow('Unauthorized');
   });
});
