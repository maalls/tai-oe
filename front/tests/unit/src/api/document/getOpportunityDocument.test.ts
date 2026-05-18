import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunityDocument } from '../../../../../src/api/document';

describe('getOpportunityDocument', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns document detail for opportunity', async () => {
      const payload = { id: 'doc-1', title: 'Doc' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunityDocument('opp-1', 'doc-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/document/doc-1?opportunity_id=opp-1');
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

      await expect(getOpportunityDocument('opp-1', 'doc-1')).rejects.toThrow(
         'Erreur lors du chargement du document'
      );
   });
});
