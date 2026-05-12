/**
 * Convert plain text URLs into clickable HTML links
 * Also handles email addresses
 */
export function linkify(text: string): string {
   if (!text) return '';

   // URL regex pattern - matches http(s):// URLs
   const urlPattern = /(https?:\/\/[^\s<>"]+)/gi;

   // Email regex pattern
   const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/gi;

   // Replace URLs with clickable links
   let linkedText = text.replace(urlPattern, (url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline break-all">${url}</a>`;
   });

   // Replace email addresses with mailto links
   linkedText = linkedText.replace(emailPattern, (email) => {
      // Don't linkify emails that are already part of an <a> tag
      if (linkedText.indexOf(`>${email}<`) !== -1) {
         return email;
      }
      return `<a href="mailto:${email}" class="text-blue-600 hover:text-blue-800 underline">${email}</a>`;
   });

   return linkedText;
}

/**
 * Linkify text and preserve line breaks by converting to <br> tags
 */
export function linkifyWithLineBreaks(text: string): string {
   if (!text) return '';

   const linkedText = linkify(text);

   // Convert newlines to <br> tags
   return linkedText.replace(/\n/g, '<br>');
}
