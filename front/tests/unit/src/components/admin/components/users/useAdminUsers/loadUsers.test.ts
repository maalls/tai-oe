import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAdminUsers } from '../../../../../../../../src/components/admin/components/users/useAdminUsers';

describe('admin/users/useAdminUsers loadUsers', () => {
   beforeEach(() => {
      vi.restoreAllMocks();
   });

   it('loads users when token and API call succeed', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockResolvedValue({
            users: [
               {
                  id: 'u-1',
                  email: 'admin@example.com',
                  full_name: 'Admin',
                  role: 'admin',
                  created_at: '2026-01-01T00:00:00Z',
               },
            ],
         }),
      });

      await model.loadUsers();

      expect(model.users.value).toHaveLength(1);
      expect(model.users.value[0].role).toBe('admin');
      expect(model.errorMessage.value).toBe('');
      expect(model.isLoading.value).toBe(false);
   });

   it('sets error message when loading fails', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockRejectedValue(new Error('Forbidden')),
      });

      await model.loadUsers();

      expect(model.users.value).toEqual([]);
      expect(model.errorMessage.value).toBe('Forbidden');
      expect(model.isLoading.value).toBe(false);
   });
});
