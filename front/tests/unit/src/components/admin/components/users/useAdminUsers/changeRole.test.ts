import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAdminUsers } from '../../../../../../../../src/components/admin/components/users/useAdminUsers';

describe('admin/users/useAdminUsers changeRole', () => {
   beforeEach(() => {
      vi.restoreAllMocks();
   });

   it('updates local user role when API call succeeds', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockResolvedValue({
            users: [
               {
                  id: 'u-1',
                  email: 'user@example.com',
                  full_name: 'User',
                  role: 'user',
                  created_at: '2026-01-01T00:00:00Z',
               },
            ],
         }),
         updateUserRole: vi.fn().mockResolvedValue({
            user: {
               id: 'u-1',
               email: 'user@example.com',
               full_name: 'User',
               role: 'admin',
               created_at: '2026-01-01T00:00:00Z',
            },
         }),
      });

      await model.loadUsers();
      await model.changeRole('u-1', 'admin');

      expect(model.users.value[0].role).toBe('admin');
      expect(model.successMessage.value).toBe('Role updated successfully.');
      expect(model.errorMessage.value).toBe('');
      expect(model.isUpdating.value).toBe(false);
      expect(model.updatingUserId.value).toBe(null);
   });

   it('sets error message when update fails', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockResolvedValue({
            users: [
               {
                  id: 'u-1',
                  email: 'user@example.com',
                  full_name: 'User',
                  role: 'user',
                  created_at: '2026-01-01T00:00:00Z',
               },
            ],
         }),
         updateUserRole: vi.fn().mockRejectedValue(new Error('Self-demotion is not allowed')),
      });

      await model.loadUsers();
      await model.changeRole('u-1', 'admin');

      expect(model.errorMessage.value).toBe('Self-demotion is not allowed');
      expect(model.isUpdating.value).toBe(false);
      expect(model.updatingUserId.value).toBe(null);
   });
});
