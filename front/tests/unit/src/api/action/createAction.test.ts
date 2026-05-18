import { afterEach, describe, expect, it, vi } from 'vitest';

import { createAction } from '../../../../../src/api/action';

describe('createAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created action', async () => {
      const data = {
         opportunity_id: 'opp-1',
         action_type: 'follow_up_email',
         schedule_type: 'daily',
         schedule_config: {},
      };
      const payload = { status: 'ok', action: { id: 'a1', ...data } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createAction(data, 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify(data),
      });
      expect(result).toEqual(payload.action);
   });

   it('throws when creation fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(
         createAction(
            {
               opportunity_id: 'opp-1',
               action_type: 'follow_up_email',
               schedule_type: 'daily',
            },
            'token-1'
         )
      ).rejects.toThrow('boom');
   });
});
