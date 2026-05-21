import { afterEach, describe, expect, it, vi } from 'vitest';

import { startOutlookOAuth } from '../../../../../src/api/outlook';

describe('startOutlookOAuth', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns auth_url from oauth start endpoint', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue({
               status: 'ok',
               auth_url: 'https://login.microsoftonline.com/authorize',
            }),
         })
      );

      const result = await startOutlookOAuth('http://localhost:3000/settings', 'u-1');

      expect(fetch).toHaveBeenCalledWith(
         expect.stringContaining(
            '/api/outlook/oauth/start?redirect_url=http%3A%2F%2Flocalhost%3A3000%2Fsettings&user_id=u-1'
         )
      );
      expect(result).toBe('https://login.microsoftonline.com/authorize');
   });
});
