import { afterEach, describe, expect, it, vi } from 'vitest';

import { createDraftOpportunity } from '../../../../../src/api/opportunity';

describe('createDraftOpportunity', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns created draft opportunity', async () => {
      const payload = { status: 'ok', opportunity: { id: 'opp-1', account_id: 'a-1' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await createDraftOpportunity('a-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunities/create-draft', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ account_id: 'a-1', name: '', source: 'user_form' }),
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

      await expect(createDraftOpportunity('a-1', 'token-1')).rejects.toThrow(
         'Erreur lors de la création de l’opportunité brouillon'
      );
   });
});
