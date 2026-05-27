import { afterEach, describe, expect, it, vi } from 'vitest';

import { listAdminUsers } from '../../../../../src/api/adminUsers';

describe('listAdminUsers', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('calls admin users endpoint with bearer token and returns payload', async () => {
      const payload = {
         users: [
            {
               id: 'u-1',
               email: 'admin@example.com',
               full_name: 'Admin',
               role: 'admin',
               created_at: '2026-01-01T00:00:00Z',
            },
         ],
      };

      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listAdminUsers('token-123', 25, 50);

      expect(fetchMock).toHaveBeenCalledWith(
         expect.stringContaining('/api/admin/users?limit=25&offset=50'),
         expect.objectContaining({
            headers: expect.objectContaining({
               Authorization: 'Bearer token-123',
            }),
         })
      );
      expect(result).toEqual(payload);
   });

   it('throws when API responds with non-ok status', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'Forbidden' }),
         })
      );

      await expect(listAdminUsers('token-123')).rejects.toThrow('Forbidden');
   });
});
