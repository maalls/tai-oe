// Run this in browser console to clear cached extraction data
// Open DevTools (Cmd+Option+I), go to Console tab, paste and run:

// Clear all extracted contact data from localStorage
Object.keys(localStorage)
  .filter((key) => key.startsWith('extracted_contact_'))
  .forEach((key) => {
    console.log('Removing:', key);
    localStorage.removeItem(key);
  });

console.log('✓ Cleared all extracted contact cache from localStorage');
