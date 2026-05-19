import { afterEach, describe, expect, it, vi } from 'vitest';

import { setupEmailRealtimeSubscription } from '../../../../../../src/components/mail/realtimeSubscription';

describe('setupEmailRealtimeSubscription', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('creates a channel subscription and forwards update payloads', async () => {
      const onEmailUpdate = vi.fn();
      const subscribe = vi.fn((statusCb) => {
         statusCb('SUBSCRIBED');
         return channel;
      });
      const on = vi.fn((_event, _filter, callback) => {
         callback({ new: { id: 'email-1', subject: 'Updated' } });
         return channel;
      });
      const channel = {
         on,
         subscribe,
         unsubscribe: vi.fn(),
      };

      const setSession = vi.fn().mockResolvedValue(undefined);
      const channelFactory = vi.fn().mockReturnValue(channel);
      const logger = { log: vi.fn(), error: vi.fn() };

      const result = await setupEmailRealtimeSubscription({
         userId: 'user-1',
         accessToken: 'access-token',
         refreshToken: 'refresh-token',
         supabaseClient: {
            auth: { setSession },
            channel: channelFactory,
         },
         onEmailUpdate,
         logger,
      });

      expect(setSession).toHaveBeenCalledWith({
         access_token: 'access-token',
         refresh_token: 'refresh-token',
      });
      expect(channelFactory).toHaveBeenCalledWith('emails:user-1');
      expect(on).toHaveBeenCalled();
      expect(subscribe).toHaveBeenCalled();
      expect(onEmailUpdate).toHaveBeenCalledWith('email-1', {
         new: { id: 'email-1', subject: 'Updated' },
      });
      expect(result).toBe(channel);
   });

   it('returns null when user id is missing', async () => {
      const logger = { log: vi.fn(), error: vi.fn() };
      const result = await setupEmailRealtimeSubscription({
         userId: '',
         supabaseClient: {
            auth: { setSession: vi.fn() },
            channel: vi.fn(),
         },
         onEmailUpdate: vi.fn(),
         logger,
      });

      expect(result).toBeNull();
      expect(logger.log).toHaveBeenCalledWith('[Realtime] No user ID, skipping subscription');
   });
});
