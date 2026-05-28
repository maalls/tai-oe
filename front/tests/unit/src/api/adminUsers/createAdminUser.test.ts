import { afterEach, describe, expect, it, vi } from 'vitest';

import { createAdminUser } from '../../../../../src/api/adminUsers';

describe('createAdminUser', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('calls create endpoint and returns created user payload', async () => {
      const payload = {
         user: {
            id: 'u-3',
            email: 'created@example.com',
            full_name: 'Created User',
            role: 'user',
            created_at: '2026-01-03T00:00:00Z',
         },
      };

      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createAdminUser('token-xyz', {
         email: 'created@example.com',
         password: 'secret-123',
         full_name: 'Created User',
         role: 'user',
      });

      expect(fetchMock).toHaveBeenCalledWith(
         expect.stringContaining('/api/admin/users'),
         expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
               Authorization: 'Bearer token-xyz',
               'Content-Type': 'application/json',
            }),
            body: JSON.stringify({
               email: 'created@example.com',
               password: 'secret-123',
               full_name: 'Created User',
               role: 'user',
            }),
         })
      );
      expect(result).toEqual(payload);
   });

   it('throws with backend message on error', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'User already registered' }),
         })
      );

      await expect(
         createAdminUser('token-xyz', {
            email: 'created@example.com',
            password: 'secret-123',
            role: 'user',
         })
      ).rejects.toThrow('User already registered');
   });
});
