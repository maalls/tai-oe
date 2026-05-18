import { afterEach, describe, expect, it, vi } from 'vitest';

import { searchOpportunities } from '../../../../../src/api/opportunity';

describe('searchOpportunities', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('loads opportunities without filters', async () => {
      const payload = { status: 'ok', opportunities: [{ id: 'opp-1' }] };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await searchOpportunities('token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunities/search', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
      expect(result).toEqual(payload.opportunities);
   });

   it('loads opportunities with name filter', async () => {
      const payload = { status: 'ok', opportunities: [{ id: 'opp-1' }] };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      await searchOpportunities('token-1', { name: 'deal test' });

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunities/search?name=deal+test', {
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(searchOpportunities('token-1', { name: 'deal' })).rejects.toThrow(
         'Erreur lors du chargement des opportunités'
      );
   });
});
