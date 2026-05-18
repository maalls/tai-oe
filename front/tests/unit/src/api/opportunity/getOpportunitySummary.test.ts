import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunitySummary } from '../../../../../src/api/opportunity';

describe('getOpportunitySummary', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns the opportunity payload', async () => {
      const payload = { status: 'ok', opportunity: { id: 'opp-1', name: 'Deal' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunitySummary('opp-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity?opportunity_id=opp-1');
      expect(result).toEqual(payload.opportunity);
   });

   it('throws when backend returns error payload', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue({ status: 'error', message: 'boom' }),
         })
      );

      await expect(getOpportunitySummary('opp-1')).rejects.toThrow('boom');
   });
});
