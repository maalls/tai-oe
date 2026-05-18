// API client for /api/account
export interface Account {
   id: string;
   name: string;
   vat_number?: string;
   siret?: string;
   address_line1?: string;
   address_line2?: string;
   postal_code?: string;
   city?: string;
   country_code?: string;
   payment_terms_default?: string;
   phone?: string;
   website?: string;
   industry?: string;
   created_at: string;
   updated_at: string;
}

export type AccountCreate = Omit<Account, 'id' | 'created_at' | 'updated_at'>;
export type AccountUpdate = Partial<AccountCreate>;

export async function listAccounts(): Promise<Account[]> {
   const res = await fetch('/api/account');
   if (!res.ok) throw new Error('Erreur lors du chargement des comptes');
   return await res.json();
}

export async function getAccount(id: string): Promise<Account> {
   const res = await fetch(`/api/account/${id}`);
   if (!res.ok) throw new Error('Compte introuvable');
   return await res.json();
}

export async function createAccount(data: AccountCreate): Promise<Account> {
   const res = await fetch('/api/account', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création du compte');
   return await res.json();
}

export async function updateAccount(id: string, data: AccountUpdate): Promise<Account> {
   const res = await fetch(`/api/account/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du compte');
   return await res.json();
}

export async function deleteAccount(id: string): Promise<{ id: string }> {
   const res = await fetch(`/api/account/${id}`, { method: 'DELETE' });
   if (!res.ok) throw new Error('Erreur lors de la suppression du compte');
   return await res.json();
}
