import { afterEach, describe, expect, it, vi } from 'vitest';

import { getActionLogs } from '../../../../../src/api/action';

describe('getActionLogs', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('loads action logs with auth token', async () => {
      const payload = { status: 'ok', logs: [{ id: 'l1' }] };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getActionLogs('a1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions/a1/logs?limit=50', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.logs);
   });

   it('throws when log loading fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(getActionLogs('a1', 'token-1')).rejects.toThrow('boom');
   });
});
