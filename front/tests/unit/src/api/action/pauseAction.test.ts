import { afterEach, describe, expect, it, vi } from 'vitest';

import { pauseAction } from '../../../../../src/api/action';

describe('pauseAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts pause request and returns action', async () => {
      const payload = { status: 'ok', action: { id: 'a1', status: 'paused' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await pauseAction('a1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions/a1/pause', {
         method: 'POST',
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.action);
   });

   it('throws when pause fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(pauseAction('a1', 'token-1')).rejects.toThrow('boom');
   });
});
