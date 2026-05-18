import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateOpportunityStageState } from '../../../../../src/api/opportunity';

describe('updateOpportunityStageState', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts stage and status payload', async () => {
      const payload = { id: 'opp-1', stage: 'CLOSED_WON', status: 'WON' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateOpportunityStageState('opp-1', 'CLOSED_WON', 'WON', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/stage-state', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ stage: 'CLOSED_WON', status: 'WON' }),
      });
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ error: 'boom' }),
         })
      );

      await expect(
         updateOpportunityStageState('opp-1', 'CLOSED_WON', 'WON', 'token-1')
      ).rejects.toThrow('boom');
   });
});