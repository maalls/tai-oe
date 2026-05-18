import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const SRC_DIR = path.join(ROOT, 'src');
const ALLOWLIST_PATH = path.join(ROOT, 'config', 'supabase-direct-allowlist.txt');

const SUPABASE_DIRECT_RE = /\bsupabase\s*\.\s*(from|rpc)\s*\(/g;

function walk(dirPath) {
   const entries = fs.readdirSync(dirPath, { withFileTypes: true });
   const files = [];
   for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      if (entry.isDirectory()) {
         files.push(...walk(fullPath));
         continue;
      }
      if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.vue'))) {
         files.push(fullPath);
      }
   }
   return files;
}

function readAllowlist() {
   const raw = fs.readFileSync(ALLOWLIST_PATH, 'utf-8');
   return new Set(
      raw
         .split(/\r?\n/)
         .map((line) => line.trim())
         .filter((line) => line && !line.startsWith('#'))
   );
}

function rel(p) {
   return path.relative(ROOT, p).replace(/\\/g, '/');
}

const allowlist = readAllowlist();
const sourceFiles = walk(SRC_DIR);

const directFiles = [];

for (const filePath of sourceFiles) {
   const content = fs.readFileSync(filePath, 'utf-8');
   SUPABASE_DIRECT_RE.lastIndex = 0;
   const hasDirect = SUPABASE_DIRECT_RE.test(content);
   if (hasDirect) {
      directFiles.push(rel(filePath));
   }
}

const unauthorized = directFiles.filter((file) => !allowlist.has(file));

if (unauthorized.length > 0) {
   console.error('Unauthorized supabase-direct files detected:');
   for (const file of unauthorized) {
      console.error(` - ${file}`);
   }
   console.error(
      '\nIf intentional, update front/config/supabase-direct-allowlist.txt in the same change with rationale.'
   );
   process.exit(1);
}

const staleAllowlistEntries = [...allowlist].filter((file) => !directFiles.includes(file));

console.log(`supabase-direct guard: ${directFiles.length} files within baseline`);
if (staleAllowlistEntries.length > 0) {
   console.log('stale allowlist entries (can be removed):');
   for (const file of staleAllowlistEntries) {
      console.log(` - ${file}`);
   }
}
