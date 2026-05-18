import { afterEach, describe, expect, it, vi } from 'vitest';

import { executeAction } from '../../../../../src/api/action';

describe('executeAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts execute request and returns payload', async () => {
      const payload = { status: 'ok', action_id: 'a1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await executeAction('a1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/action/a1/execute', {
         method: 'POST',
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload);
   });

   it('throws when execution fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(executeAction('a1', 'token-1')).rejects.toThrow('boom');
   });
});
