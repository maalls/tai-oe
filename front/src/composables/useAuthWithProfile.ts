import { ref, computed, onMounted } from 'vue';
import { useAuth } from '../stores/auth';
import { fetchAuthUser } from '../api/authUser';

// Singleton partagé
export const userRole = ref<string | null>(null);
export const profileLoading = ref(false);
export const profileError = ref<string | null>(null);

export async function fetchUserRole() {
   profileLoading.value = true;
   profileError.value = null;
   try {
      const { getValidToken } = useAuth();
      const token = await getValidToken();
      const payload = await fetchAuthUser(token);
      userRole.value = payload.user?.role || null;
   } catch (e: any) {
      userRole.value = null;
      profileError.value = e?.message || 'Erreur lors de la récupération du rôle';
   } finally {
      profileLoading.value = false;
   }
}

export function useAuthWithProfile() {
   const {
      user,
      session,
      isAuthenticated,
      loading,
      signUp,
      signIn,
      signOut,
      updateDisplayName,
      initialize,
      getValidToken,
   } = useAuth();

   onMounted(() => {
      fetchUserRole();
   });

   return {
      user,
      session,
      isAuthenticated,
      loading,
      signUp,
      signIn,
      signOut,
      updateDisplayName,
      initialize,
      getValidToken,
      userRole,
      profileLoading,
      profileError,
      fetchUserRole,
   };
}
