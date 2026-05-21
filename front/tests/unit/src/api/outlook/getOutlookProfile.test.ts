import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOutlookProfile } from '../../../../../src/api/outlook';

describe('getOutlookProfile', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns profile payload when endpoint succeeds', async () => {
      const payload = { status: 'ok', profile: { mail: 'user@example.com' } };
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue(payload),
         })
      );

      const result = await getOutlookProfile('u-1');

      expect(fetch).toHaveBeenCalledWith(
         expect.stringContaining('/api/outlook/profile?user_id=u-1')
      );
      expect(result).toEqual(payload);
   });
});
