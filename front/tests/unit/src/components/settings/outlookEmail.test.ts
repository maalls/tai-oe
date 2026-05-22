import { describe, expect, it } from 'vitest';

import { getOutlookDisplayEmail } from '../../../../../src/components/settings/outlookEmail';

describe('getOutlookDisplayEmail', () => {
   it('prefers the mailbox address when available', () => {
      const result = getOutlookDisplayEmail({
         mail: 'user@example.com',
         preferred_username: 'user@tenant.onmicrosoft.com',
         userPrincipalName: 'user_example.com#EXT#@tenant.onmicrosoft.com',
      });

      expect(result).toBe('user@example.com');
   });

   it('decodes guest user principal names when mail is missing', () => {
      const result = getOutlookDisplayEmail({
         userPrincipalName: 'maalls_hotmail.com#EXT#@maallshotmail.onmicrosoft.com',
      });

      expect(result).toBe('maalls@hotmail.com');
   });
});
