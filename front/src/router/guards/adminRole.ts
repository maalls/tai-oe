import { fetchAuthUser } from '../../api/authUser';

export type ResolveAdminAccessInput = {
   requiresAdmin: boolean;
   getValidToken: () => Promise<string>;
};

export async function resolveAdminAccess(input: ResolveAdminAccessInput): Promise<boolean> {
   if (!input.requiresAdmin) {
      return true;
   }

   try {
      const token = await input.getValidToken();
      const payload = await fetchAuthUser(token);
      const role = payload?.user?.role;
      return role === 'admin';
   } catch {
      return false;
   }
}
