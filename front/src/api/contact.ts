export interface Contact {
   id: string;
   account_id: string;
   name: string;
   email?: string | null;
   phone?: string | null;
   role_title?: string | null;
   created_at: string;
   account_name?: string | null;
}

export type ContactCreate = Omit<Contact, 'id' | 'created_at' | 'account_name'>;
export type ContactUpdate = Partial<ContactCreate>;

export async function listContacts(): Promise<Contact[]> {
   const res = await fetch('/api/contact');
   if (!res.ok) throw new Error('Erreur lors du chargement des contacts');
   return await res.json();
}

export async function getContact(id: string): Promise<Contact> {
   const res = await fetch(`/api/contact/${id}`);
   if (!res.ok) throw new Error('Contact introuvable');
   return await res.json();
}

export async function createContact(data: ContactCreate): Promise<Contact> {
   const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création du contact');
   return await res.json();
}

export async function updateContact(id: string, data: ContactUpdate): Promise<Contact> {
   const res = await fetch(`/api/contact/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du contact');
   return await res.json();
}

export async function deleteContact(id: string): Promise<{ id: string }> {
   const res = await fetch(`/api/contact/${id}`, { method: 'DELETE' });
   if (!res.ok) throw new Error('Erreur lors de la suppression du contact');
   return await res.json();
}
