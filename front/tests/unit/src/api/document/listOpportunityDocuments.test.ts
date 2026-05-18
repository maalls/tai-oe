import { afterEach, describe, expect, it, vi } from 'vitest';

import { listOpportunityDocuments } from '../../../../../src/api/document';

describe('listOpportunityDocuments', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns document list for opportunity', async () => {
      const payload = [{ id: 'doc-1', title: 'Doc' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listOpportunityDocuments('opp-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/document?opportunity_id=opp-1');
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

      await expect(listOpportunityDocuments('opp-1')).rejects.toThrow(
         'Erreur lors du chargement des documents'
      );
   });
});
