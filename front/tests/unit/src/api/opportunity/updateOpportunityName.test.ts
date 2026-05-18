import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateOpportunityName } from '../../../../../src/api/opportunity';

describe('updateOpportunityName', () => {
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

      const result = await updateOpportunityName('opp-1', 'Updated', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/name', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ name: 'Updated' }),
      });
      expect(result).toEqual(payload);
   });
});
