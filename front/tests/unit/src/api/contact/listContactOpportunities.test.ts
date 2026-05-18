import { afterEach, describe, expect, it, vi } from 'vitest';

import { listContactOpportunities } from '../../../../../src/api/contact';

describe('listContactOpportunities', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns related opportunities', async () => {
      const payload = [{ id: 'opp-1', name: 'Deal', stage: 'NEW_LEAD', role: 'decision_maker' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listContactOpportunities('c-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/contact/c-1/opportunities');
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

      await expect(listContactOpportunities('c-1')).rejects.toThrow(
         'Erreur lors du chargement des opportunités liées'
      );
   });
});
