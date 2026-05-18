import { afterEach, describe, expect, it, vi } from 'vitest';

import { listEmailAttachments } from '../../../../../src/api/email';

describe('listEmailAttachments', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns attachments payload', async () => {
      const payload = {
         attachments: [{ id: 'att-1', filename: 'quote.pdf' }],
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listEmailAttachments('e-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/email/e-1/attachments', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.attachments);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ error: 'Unauthorized' }),
         })
      );

      await expect(listEmailAttachments('e-1', 'token-1')).rejects.toThrow('Unauthorized');
   });
});