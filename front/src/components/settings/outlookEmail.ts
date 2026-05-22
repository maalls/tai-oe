type OutlookProfile = {
   mail?: string | null;
   preferred_username?: string | null;
   userPrincipalName?: string | null;
};

function decodeGuestUserPrincipalName(userPrincipalName: string): string {
   const guestSuffixIndex = userPrincipalName.indexOf('#EXT#@');
   if (guestSuffixIndex <= 0) {
      return userPrincipalName;
   }

   const guestPrefix = userPrincipalName.slice(0, guestSuffixIndex);
   const decodedEmail = guestPrefix.replace('_', '@');
   return decodedEmail || userPrincipalName;
}

export function getOutlookDisplayEmail(profile?: OutlookProfile | null): string {
   const mail = profile?.mail?.trim();
   if (mail) {
      return mail;
   }

   const preferredUsername = profile?.preferred_username?.trim();
   if (preferredUsername) {
      return preferredUsername;
   }

   const userPrincipalName = profile?.userPrincipalName?.trim();
   if (!userPrincipalName) {
      return '';
   }

   return decodeGuestUserPrincipalName(userPrincipalName);
}