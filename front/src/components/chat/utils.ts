/**
 * Chat utilities (formatting, scrolling)
 */

export function formatToolContent(content: string | null): string {
   if (!content) return '';
   try {
      const obj = JSON.parse(content);
      return JSON.stringify(obj, null, 2);
   } catch {
      return String(content);
   }
}
