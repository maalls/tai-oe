import { afterEach, describe, expect, it, vi } from 'vitest';

import { extractOpportunityAuthorContact } from '../../../../../src/api/opportunity';

describe('extractOpportunityAuthorContact', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('posts payload and returns extraction result', async () => {
      const payload = { status: 'ok', contact_id: 'c-1', linked: true };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await extractOpportunityAuthorContact(
         'opp-1',
         'alice@example.com',
         'Alice',
         'token-1'
      );

      expect(fetchMock).toHaveBeenCalledWith('/api/opportunity/opp-1/extract-author-contact', {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ from_email: 'alice@example.com', from_name: 'Alice' }),
      });
      expect(result).toEqual(payload);
   });
});
