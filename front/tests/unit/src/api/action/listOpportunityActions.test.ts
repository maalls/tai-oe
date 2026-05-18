import { afterEach, describe, expect, it, vi } from 'vitest';

import { listOpportunityActions } from '../../../../../src/api/action';

describe('listOpportunityActions', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('loads opportunity actions with auth token', async () => {
      const payload = { status: 'ok', actions: [{ id: 'a1' }] };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listOpportunityActions('opp-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunities/opp-1/actions', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.actions);
   });

   it('throws when loading fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(listOpportunityActions('opp-1', 'token-1')).rejects.toThrow('boom');
   });
});
