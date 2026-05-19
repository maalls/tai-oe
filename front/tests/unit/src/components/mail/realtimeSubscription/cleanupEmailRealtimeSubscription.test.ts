import { afterEach, describe, expect, it, vi } from 'vitest';

import { cleanupEmailRealtimeSubscription } from '../../../../../../src/components/mail/realtimeSubscription';

describe('cleanupEmailRealtimeSubscription', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('unsubscribes an active channel and returns null', () => {
      const unsubscribe = vi.fn();
      const logger = { log: vi.fn(), error: vi.fn() };

      const result = cleanupEmailRealtimeSubscription(
         {
            unsubscribe,
            on: vi.fn(),
            subscribe: vi.fn(),
         },
         logger
      );

      expect(unsubscribe).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
   });

   it('returns null when there is no subscription', () => {
      const logger = { log: vi.fn(), error: vi.fn() };

      const result = cleanupEmailRealtimeSubscription(null, logger);

      expect(result).toBeNull();
      expect(logger.log).not.toHaveBeenCalled();
   });
});
