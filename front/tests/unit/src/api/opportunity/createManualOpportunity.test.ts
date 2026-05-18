import { afterEach, describe, expect, it, vi } from 'vitest';

import { createManualOpportunity } from '../../../../../src/api/opportunity';

describe('createManualOpportunity', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created opportunity', async () => {
      const payload = { status: 'ok', opportunity: { id: 'opp-1', name: 'New Opportunity' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createManualOpportunity('New Opportunity', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunities/create-manual', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ name: 'New Opportunity' }),
      });
      expect(result).toEqual(payload.opportunity);
   });

   it('throws when creation fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(createManualOpportunity('New Opportunity', 'token-1')).rejects.toThrow(
         'Erreur lors de la création de l’opportunité'
      );
   });
});
