import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateAction } from '../../../../../src/api/action';

describe('updateAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts payload and returns updated action', async () => {
      const data = {
         action_type: 'follow_up_email',
         schedule_type: 'weekly',
         schedule_config: {},
      };
      const payload = { status: 'ok', action: { id: 'a1', ...data } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateAction('a1', data, 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions/a1', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify(data),
      });
      expect(result).toEqual(payload.action);
   });

   it('throws when update fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(
         updateAction(
            'a1',
            {
               action_type: 'follow_up_email',
               schedule_type: 'weekly',
            },
            'token-1'
         )
      ).rejects.toThrow('boom');
   });
});
