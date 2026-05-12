# Supabase Realtime Debugging Guide

## Issue
Realtime subscriptions are implemented in `front/src/components/MailPage.vue` but frontend updates from database changes are not appearing, even though the data is being saved successfully.

## What's Been Done
1. ✅ Updated `MailPage.vue` to initialize Supabase client with realtime config
2. ✅ Added `setupRealtimeSubscription()` function that:
   - Creates channel: `emails:${userId}`
   - Listens for UPDATE events on `public.emails` table
   - Filters by `user_id=eq.${userId}`
   - Updates local `messages.value[index]` when changes are received
3. ✅ Added JWT token authentication via `supabase.auth.setSession()`
4. ✅ Added comprehensive console.log debugging with `[Realtime]` prefix
5. ✅ Updated schema to enable realtime publication: `ALTER PUBLICATION supabase_realtime ADD TABLE emails`

## Debug Steps

### Step 1: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Open the email classifier page
4. You should see logs like:
   ```
   [Realtime] User authenticated, setting up subscription
   [Realtime] Setting up subscription for user: [UUID]
   [Realtime] Supabase URL: http://localhost:8003
   [Realtime] Creating channel: emails:[UUID]
   [Realtime] Subscription status: ...
   ```

4. Click "Classify" on an email
5. Look for logs like:
   ```
   [Realtime] Email UPDATE received: ...
   [Realtime] Updated email successfully: [UUID]
   ```

### Step 2: Verify Supabase Connection
Check if session/JWT token is being passed:
```
[Realtime] Token available: true/false
[Realtime] Auth session set
```

### Step 3: Enable Realtime on Supabase

The emails table must have realtime enabled. Run this SQL on your Supabase instance:

```sql
-- Enable realtime for emails and email_labels tables
ALTER PUBLICATION supabase_realtime ADD TABLE emails;
ALTER PUBLICATION supabase_realtime ADD TABLE email_labels;
```

How to run this:
1. In Supabase Dashboard → SQL Editor
2. Paste the SQL above
3. Click "Run"

Or if using `supabase start` locally:
1. Connect to local Postgres: `psql postgresql://postgres:postgres@localhost:5432/postgres`
2. Run the SQL commands above

### Step 4: Check RLS Policies
The RLS policies look correct - they use `(select auth.uid())` which should work with realtime. However, verify that:
- User is authenticated with valid JWT
- The `auth.uid()` from JWT matches the `user_id` in emails table

### Step 5: Test Realtime Connectivity
Open browser console and run:
```javascript
// Test if Supabase client is connected
console.log(supabase)  // Should show Supabase client object

// Manually trigger a subscription test
const channel = supabase
  .channel('test-channel')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'emails' },
    payload => console.log('REALTIME TEST:', payload)
  )
  .subscribe(status => console.log('REALTIME STATUS:', status))
```

## Common Issues

### Issue: Subscription created but no events received
- **Cause**: Realtime not enabled on table
- **Solution**: Run SQL commands from Step 3
- **Check**: Query `SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';` - should include 'emails'

### Issue: Auth token not included
- **Cause**: `session.value?.session?.access_token` might be undefined
- **Solution**: Add logging to check token value
- **Check**: Browser console should show `[Realtime] Token available: true`

### Issue: RLS policies blocking realtime
- **Cause**: User ID mismatch between JWT and database
- **Solution**: Verify `auth.uid()` in RLS policies matches `session.value?.user?.id`
- **Check**: Backend logs should show correct `user_id` for classify requests

### Issue: Channel filter syntax wrong
- **Current**: `filter: 'user_id=eq.${userId}'`
- **Check**: PostgreSQL Realtime filter syntax is correct
- **Debug**: Remove filter temporarily to receive ALL updates

## Next Steps if Realtime Still Doesn't Work

1. Implement polling fallback in `handleClassify()`:
   ```typescript
   // After classification succeeds, poll for updates every 1 second for 10 seconds
   let attempts = 0;
   const pollInterval = setInterval(() => {
     loadMessages(false);
     attempts++;
     if (attempts >= 10) clearInterval(pollInterval);
   }, 1000);
   ```

2. Or add manual refetch button to UI

3. Consider using simpler approach: 
   - Skip realtime entirely
   - Just refetch after classification succeeds
   - This guarantees UI stays in sync

## Files Modified
- `front/src/components/MailPage.vue` - Added realtime subscription logic
- `back/schema/emails.sql` - Added `ALTER PUBLICATION` commands
