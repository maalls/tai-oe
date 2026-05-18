import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunityStageHistory } from '../../../../../src/api/opportunity';

describe('getOpportunityStageHistory', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('gets stage history list', async () => {
      const payload = [{ opportunity_id: 'opp-1', from_stage: 'PAID', to_stage: 'CLOSED_WON' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunityStageHistory('opp-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/stage-history?limit=10');
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getOpportunityStageHistory('opp-1')).rejects.toThrow(
         'Erreur lors du chargement de l’historique des stages'
      );
   });
});