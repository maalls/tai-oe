import { afterEach, describe, expect, it, vi } from 'vitest';

import { getOpportunitySentEmail } from '../../../../../src/api/opportunity';

describe('getOpportunitySentEmail', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns sent_email payload when present', async () => {
      const payload = { sent_email: { id: 'mail-1', document_id: 'doc-1' } };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getOpportunitySentEmail('opp-1', 'doc-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/sent-email?document_id=doc-1');
      expect(result).toEqual(payload.sent_email);
   });

   it('returns null when backend has no sent_email', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue({ sent_email: null }),
         })
      );

      const result = await getOpportunitySentEmail('opp-1');

      expect(result).toBeNull();
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getOpportunitySentEmail('opp-1')).rejects.toThrow(
         'Erreur lors du chargement de l’email envoyé'
      );
   });
});
