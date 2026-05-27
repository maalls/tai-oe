import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateAdminUserRole } from '../../../../../src/api/adminUsers';

describe('updateAdminUserRole', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('calls role update endpoint and returns updated user', async () => {
      const payload = {
         user: {
            id: 'u-2',
            email: 'user@example.com',
            full_name: 'User',
            role: 'admin',
            created_at: '2026-01-02T00:00:00Z',
         },
      };

      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateAdminUserRole('token-abc', 'u-2', 'admin');

      expect(fetchMock).toHaveBeenCalledWith(
         expect.stringContaining('/api/admin/users/u-2/role'),
         expect.objectContaining({
            method: 'PATCH',
            headers: expect.objectContaining({
               Authorization: 'Bearer token-abc',
               'Content-Type': 'application/json',
            }),
            body: JSON.stringify({ role: 'admin' }),
         })
      );
      expect(result).toEqual(payload);
   });

   it('throws with backend message on error', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'Invalid role' }),
         })
      );

      await expect(updateAdminUserRole('token-abc', 'u-2', 'owner' as any)).rejects.toThrow(
         'Invalid role'
      );
   });
});
