import { afterEach, describe, expect, it, vi } from 'vitest';

import { revokeOutlook } from '../../../../../src/api/outlook';

describe('revokeOutlook', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts to revoke endpoint and returns payload', async () => {
      const payload = { status: 'ok', message: 'revoked' };
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue(payload),
         })
      );

      const result = await revokeOutlook('u-1');

      expect(fetch).toHaveBeenCalledWith(
         expect.stringContaining('/api/outlook/revoke?user_id=u-1'),
         {
            method: 'POST',
         }
      );
      expect(result).toEqual(payload);
   });
});
