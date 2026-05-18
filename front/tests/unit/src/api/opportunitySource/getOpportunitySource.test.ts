import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunitySource } from '../../../../../src/api/opportunitySource';

describe('getOpportunitySource', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns source payload for an opportunity', async () => {
      const payload = {
         source_type: 'email',
         email: { id: 'em-1' },
         document: null,
         participants: [],
         attachments: [],
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunitySource('opp-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/source');
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

      await expect(getOpportunitySource('opp-1')).rejects.toThrow(
         'Erreur lors du chargement de la source opportunité'
      );
   });
});
