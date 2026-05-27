import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('admin users route', () => {
   it('declares /admin/users route with auth meta', () => {
      const routerFilePath = resolve(process.cwd(), 'src/router/index.ts');
      const routerSource = readFileSync(routerFilePath, 'utf-8');

      expect(routerSource).toContain("path: '/admin/users'");
      expect(routerSource).toContain("name: 'admin-users'");
      expect(routerSource).toContain("titleKey: 'pageTitles.adminUsers'");
   });
});
