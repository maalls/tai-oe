type RealtimeChannel = {
   unsubscribe: () => unknown;
   on: (...args: any[]) => RealtimeChannel;
   subscribe: (...args: any[]) => RealtimeChannel;
};

type SupabaseLike = {
   auth: {
      setSession: (session: { access_token: string; refresh_token: string }) => Promise<unknown>;
   };
   channel: (name: string) => RealtimeChannel;
};

type Logger = Pick<Console, 'log' | 'error'>;

export async function setupEmailRealtimeSubscription(params: {
   userId: string;
   accessToken?: string;
   refreshToken?: string;
   supabaseClient: SupabaseLike;
   onEmailUpdate: (emailId: string, payload: any) => void;
   logger?: Logger;
}): Promise<RealtimeChannel | null> {
   const {
      userId,
      accessToken,
      refreshToken,
      supabaseClient,
      onEmailUpdate,
      logger = console,
   } = params;

   if (!userId) {
      logger.log('[Realtime] No user ID, skipping subscription');
      return null;
   }

   logger.log('[Realtime] Setting up subscription for user:', userId);

   try {
      if (accessToken) {
         await supabaseClient.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken || '',
         });
      }

      const channel = supabaseClient
         .channel(`emails:${userId}`)
         .on(
            'postgres_changes',
            {
               event: 'UPDATE',
               schema: 'public',
               table: 'emails',
               filter: `user_id=eq.${userId}`,
            },
            (payload: any) => {
               if (payload.new?.id) {
                  onEmailUpdate(payload.new.id, payload);
               }
            }
         )
         .subscribe((status: string, err?: any) => {
            logger.log('[Realtime] Subscription status changed:', status);
            if (err) {
               logger.error('[Realtime] Subscription error:', err);
            }
         });

      return channel;
   } catch (error) {
      logger.error('[Realtime] Error setting up subscription:', error);
      return null;
   }
}

export function cleanupEmailRealtimeSubscription(
   subscription: RealtimeChannel | null,
   logger: Logger = console
): null {
   if (!subscription) {
      return null;
   }

   logger.log('[Realtime] Cleaning up subscription...');
   try {
      subscription.unsubscribe();
      logger.log('[Realtime] Subscription unsubscribed successfully');
   } catch (error) {
      logger.error('[Realtime] Error unsubscribing:', error);
   }

   return null;
}
