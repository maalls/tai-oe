import { afterEach, describe, expect, it, vi } from 'vitest';

import { resolveAdminAccess } from '../../../../../../src/router/guards/adminRole';
import * as authUserApi from '../../../../../../src/api/authUser';

describe('resolveAdminAccess', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns true when route does not require admin', async () => {
      const result = await resolveAdminAccess({
         requiresAdmin: false,
         getValidToken: vi.fn(),
      });

      expect(result).toBe(true);
   });

   it('returns true for admin user', async () => {
      vi.spyOn(authUserApi, 'fetchAuthUser').mockResolvedValue({
         user: { id: 'u-1', role: 'admin' },
      });

      const result = await resolveAdminAccess({
         requiresAdmin: true,
         getValidToken: vi.fn().mockResolvedValue('token-1'),
      });

      expect(result).toBe(true);
   });

   it('returns false for non-admin user', async () => {
      vi.spyOn(authUserApi, 'fetchAuthUser').mockResolvedValue({
         user: { id: 'u-1', role: 'user' },
      });

      const result = await resolveAdminAccess({
         requiresAdmin: true,
         getValidToken: vi.fn().mockResolvedValue('token-1'),
      });

      expect(result).toBe(false);
   });

   it('returns false when auth user fetch fails', async () => {
      vi.spyOn(authUserApi, 'fetchAuthUser').mockRejectedValue(new Error('boom'));

      const result = await resolveAdminAccess({
         requiresAdmin: true,
         getValidToken: vi.fn().mockResolvedValue('token-1'),
      });

      expect(result).toBe(false);
   });
});
