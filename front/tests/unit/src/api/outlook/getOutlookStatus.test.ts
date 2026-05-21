import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOutlookStatus } from '../../../../../src/api/outlook';

describe('getOutlookStatus', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('calls outlook status endpoint with user_id and returns payload', async () => {
      const payload = { status: 'ok', authorized: true };
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue(payload),
         })
      );

      const result = await getOutlookStatus('u-1');

      expect(fetch).toHaveBeenCalledWith(
         expect.stringContaining('/api/outlook/status?user_id=u-1')
      );
      expect(result).toEqual(payload);
   });
});
