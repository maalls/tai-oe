import { afterEach, describe, expect, it, vi } from 'vitest';

describe('useAuth.signOut', () => {
   afterEach(() => {
      vi.restoreAllMocks();
      vi.resetModules();
   });

   it('clears user and session after successful sign out', async () => {
      const session = {
         access_token: 'token-123',
         user: { id: 'user-1', email: 'user@example.com' },
      } as any;

      const signInWithPassword = vi.fn().mockResolvedValue({
         data: {
            user: session.user,
            session,
         },
         error: null,
      });

      const signOut = vi.fn().mockResolvedValue({ error: null });

      vi.doMock('../../../../../../src/lib/supabase', () => ({
         supabase: {
            auth: {
               signUp: vi.fn(),
               signInWithPassword,
               signOut,
               getSession: vi.fn(),
               updateUser: vi.fn(),
               onAuthStateChange: vi.fn(),
            },
         },
      }));

      vi.doMock('../../../../../../src/api/profile', () => ({
         fetchProfile: vi.fn(),
         updateProfile: vi.fn(),
      }));

      const { useAuth } = await import('../../../../../../src/stores/auth');
      const auth = useAuth();

      await auth.signIn('user@example.com', 'password');
      expect(auth.isAuthenticated.value).toBe(true);

      await auth.signOut();

      expect(signOut).toHaveBeenCalledTimes(1);
      expect(auth.user.value).toBeNull();
      expect(auth.session.value).toBeNull();
      expect(auth.isAuthenticated.value).toBe(false);
   });

   it('throws when supabase returns sign out error', async () => {
      const signOut = vi.fn().mockResolvedValue({
         error: new Error('signout failed'),
      });

      vi.doMock('../../../../../../src/lib/supabase', () => ({
         supabase: {
            auth: {
               signUp: vi.fn(),
               signInWithPassword: vi.fn(),
               signOut,
               getSession: vi.fn(),
               updateUser: vi.fn(),
               onAuthStateChange: vi.fn(),
            },
         },
      }));

      vi.doMock('../../../../../../src/api/profile', () => ({
         fetchProfile: vi.fn(),
         updateProfile: vi.fn(),
      }));

      const { useAuth } = await import('../../../../../../src/stores/auth');
      const auth = useAuth();

      await expect(auth.signOut()).rejects.toThrow('signout failed');
   });
});
