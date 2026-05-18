export interface ProductDetail {
   id: string | number;
   marque?: string;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   family_codes?: string[];
   vector_text?: string;
}

export async function getProduct(productId: string): Promise<ProductDetail> {
   const res = await fetch(`/api/products/${encodeURIComponent(productId)}`);
   if (!res.ok) throw new Error('Erreur lors du chargement du produit');
   return await res.json();
}
