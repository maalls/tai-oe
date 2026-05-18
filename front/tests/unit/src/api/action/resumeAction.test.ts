import { afterEach, describe, expect, it, vi } from 'vitest';

import { resumeAction } from '../../../../../src/api/action';

describe('resumeAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts resume request and returns action', async () => {
      const payload = { status: 'ok', action: { id: 'a1', status: 'active' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await resumeAction('a1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions/a1/resume', {
         method: 'POST',
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.action);
   });

   it('throws when resume fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(resumeAction('a1', 'token-1')).rejects.toThrow('boom');
   });
});
