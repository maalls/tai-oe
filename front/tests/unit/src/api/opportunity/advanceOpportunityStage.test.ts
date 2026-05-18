import { afterEach, describe, expect, it, vi } from 'vitest';

import { advanceOpportunityStage } from '../../../../../src/api/opportunity';

describe('advanceOpportunityStage', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns result', async () => {
      const payload = { status: 'ok', opportunity: { id: 'opp-1', stage: 'INVOICED' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await advanceOpportunityStage('opp-1', 'INVOICED');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/advance', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ opportunity_id: 'opp-1', stage: 'INVOICED' }),
      });
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(advanceOpportunityStage('opp-1', 'INVOICED')).rejects.toThrow('boom');
   });

   it('throws when backend returns status error', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue({ status: 'error', message: 'bad stage' }),
         })
      );

      await expect(advanceOpportunityStage('opp-1', 'INVOICED')).rejects.toThrow('bad stage');
   });
});
