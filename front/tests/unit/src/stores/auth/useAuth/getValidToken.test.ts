import { afterEach, describe, expect, it, vi } from 'vitest';

describe('useAuth.getValidToken', () => {
   afterEach(() => {
      vi.restoreAllMocks();
      vi.resetModules();
   });

   it('returns access token and updates auth state from session', async () => {
      const session = {
         access_token: 'token-123',
         refresh_token: 'refresh-123',
         expires_at: Math.floor(Date.now() / 1000) + 3600,
         user: { id: 'user-1', email: 'user@example.com' },
      } as any;

      const refreshSession = vi.fn().mockResolvedValue({
         data: { session },
         error: null,
      });

      vi.doMock('../../../../../../src/lib/supabase', () => ({
         supabase: {
            auth: {
               getSession: vi.fn().mockResolvedValue({
                  data: { session },
               }),
               refreshSession,
               getUser: vi.fn().mockResolvedValue({ error: null }),
               signUp: vi.fn(),
               signInWithPassword: vi.fn(),
               signOut: vi.fn(),
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

      const token = await auth.getValidToken();

      expect(token).toBe('token-123');
      expect(auth.session.value).toEqual(session);
      expect(auth.user.value).toEqual(session.user);
      expect(refreshSession).not.toHaveBeenCalled();
   });

   it('throws when no valid session token exists', async () => {
      const refreshSession = vi.fn().mockResolvedValue({
         data: { session: null },
         error: new Error('session_not_found'),
      });

      vi.doMock('../../../../../../src/lib/supabase', () => ({
         supabase: {
            auth: {
               getSession: vi.fn().mockResolvedValue({
                  data: { session: null },
               }),
               refreshSession,
               getUser: vi.fn(),
               signUp: vi.fn(),
               signInWithPassword: vi.fn(),
               signOut: vi.fn(),
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

      await expect(auth.getValidToken()).rejects.toThrow('Session expired, please sign in again');
      expect(refreshSession).toHaveBeenCalledTimes(1);
   });
});
