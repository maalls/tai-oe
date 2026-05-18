import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunityInvoiceView } from '../../../../../src/api/invoice';

describe('getOpportunityInvoiceView', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns aggregated invoice payload', async () => {
      const payload = {
         invoice: { id: 'inv-1', type: 'INVOICE' },
         sent_email: { id: 'sent-1' },
         default_contact: { id: 'contact-1', email: 'buyer@example.com' },
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunityInvoiceView('opp-1', 'inv-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/invoice/inv-1/view?opportunity_id=opp-1');
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

      await expect(getOpportunityInvoiceView('opp-1', 'inv-1')).rejects.toThrow(
         'Erreur lors du chargement de la facture'
      );
   });
});
