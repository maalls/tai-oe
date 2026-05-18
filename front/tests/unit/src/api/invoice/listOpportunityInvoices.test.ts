import { afterEach, describe, expect, it, vi } from 'vitest';

import { listOpportunityInvoices } from '../../../../../src/api/invoice';

describe('listOpportunityInvoices', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns invoice list for opportunity', async () => {
      const payload = [{ id: 'inv-1', type: 'INVOICE' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listOpportunityInvoices('opp-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/invoice?opportunity_id=opp-1');
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

      await expect(listOpportunityInvoices('opp-1')).rejects.toThrow(
         'Erreur lors du chargement des factures'
      );
   });
});
