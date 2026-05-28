import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAdminUsers } from '../../../../../../../../src/components/admin/components/users/useAdminUsers';

describe('admin/users/useAdminUsers addUser', () => {
   beforeEach(() => {
      vi.restoreAllMocks();
   });

   it('prepends created user when API call succeeds', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockResolvedValue({
            users: [
               {
                  id: 'u-1',
                  email: 'existing@example.com',
                  full_name: 'Existing',
                  role: 'user',
                  created_at: '2026-01-01T00:00:00Z',
               },
            ],
         }),
         createUser: vi.fn().mockResolvedValue({
            user: {
               id: 'u-2',
               email: 'created@example.com',
               full_name: 'Created',
               role: 'admin',
               created_at: '2026-01-02T00:00:00Z',
            },
         }),
      });

      await model.loadUsers();
      await model.addUser({
         email: 'created@example.com',
         password: 'secret-123',
         full_name: 'Created',
         role: 'admin',
      });

      expect(model.users.value).toHaveLength(2);
      expect(model.users.value[0].id).toBe('u-2');
      expect(model.successMessage.value).toBe('User created successfully.');
      expect(model.errorMessage.value).toBe('');
      expect(model.isCreating.value).toBe(false);
   });

   it('sets error message when creation fails', async () => {
      const model = useAdminUsers({
         getValidToken: vi.fn().mockResolvedValue('token-1'),
         listUsers: vi.fn().mockResolvedValue({ users: [] }),
         createUser: vi.fn().mockRejectedValue(new Error('User already registered')),
      });

      await model.loadUsers();
      await model.addUser({
         email: 'created@example.com',
         password: 'secret-123',
         role: 'user',
      });

      expect(model.errorMessage.value).toBe('User already registered');
      expect(model.isCreating.value).toBe(false);
   });
});
