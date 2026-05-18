import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateOpportunityAccount } from '../../../../../src/api/opportunity';

describe('updateOpportunityAccount', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('puts payload and returns updated opportunity', async () => {
      const payload = { id: 'opp-1', account_id: 'a-1', name: 'Updated' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateOpportunityAccount('opp-1', 'a-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/account', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ account_id: 'a-1' }),
      });
      expect(result).toEqual(payload);
   });

   it('throws when update fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(updateOpportunityAccount('opp-1', 'a-1', 'token-1')).rejects.toThrow(
         'Erreur lors de la mise à jour du compte de l’opportunité'
      );
   });
});