import { ref, computed, onMounted } from 'vue';
import { useAuth } from './auth';
import { fetchAuthUser } from '../api/authUser';

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
   const userRole = ref<string | null>(null);
   const profileLoading = ref(false);
   const profileError = ref<string | null>(null);

   async function fetchUserRole() {
      profileLoading.value = true;
      profileError.value = null;
      try {
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
