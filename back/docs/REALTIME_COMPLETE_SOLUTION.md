# Supabase Realtime Sync - Complete Solution

## Overview
Implemented full Supabase Realtime infrastructure to automatically sync email classifications from database to frontend UI in real-time.

**Status:** ✅ Implementation Complete - Ready for Testing

## What Was Implemented

### Frontend Changes (MailPage.vue)
```typescript
// 1. Enhanced Supabase Client
const supabase = createClient(
   import.meta.env.VITE_SUPABASE_URL,
   import.meta.env.VITE_SUPABASE_ANON_KEY,
   {
      realtime: { params: { eventsPerSecond: 10 } },
      auth: { persistSession: false },
   }
);

// 2. JWT Authentication
const token = session.value?.access_token;
await supabase.auth.setSession({
   access_token: token,
   refresh_token: session.value?.refresh_token || '',
});

// 3. Realtime Subscription
emailSubscription = supabase
   .channel(`emails:${userId}`)
   .on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: 'emails',
      filter: `user_id=eq.${userId}`,
   }, (payload) => {
      // Update UI with new classification data
      messages.value[index] = {
         ...messages.value[index],
         category_suggestion: payload.new.category_suggestion,
         classification_reason: payload.new.classification_reason,
         classified_at: payload.new.classified_at,
         is_classified: payload.new.is_classified,
      };
   })
   .subscribe();

// 4. Comprehensive Logging
console.log('[Realtime] Setting up subscription for user:', userId);
console.log('[Realtime] Token available:', !!token);
console.log('[Realtime] Subscription status:', status);
console.log('[Realtime] Email UPDATE received:', payload);
```

### Database Changes (emails.sql)
```sql
-- Enable realtime publication on tables
ALTER PUBLICATION supabase_realtime ADD TABLE emails;
ALTER PUBLICATION supabase_realtime ADD TABLE email_labels;
```

### Type Fixes (MailPage.vue)
```typescript
interface Message {
   id: string;
   provider?: string;
   is_classified?: boolean;
   category_suggestion?: string;
   classification_reason?: string;
   classified_at?: string;
   [key: string]: any; // Allow other fields from API
}
```

## Data Flow

```
User Classifies Email
        ↓
Frontend calls /api/emails/classify/{uuid}
        ↓
Backend LLM classifies and saves to DB
        ↓
PostgreSQL triggers realtime event
        ↓
Supabase publishes UPDATE event
        ↓
Frontend receives event via subscription
        ↓
Vue updates messages.value array reactively
        ↓
UI re-renders with new classification
```

## Setup Instructions

### 1. Enable Realtime in Supabase (REQUIRED)

Run this SQL on your Supabase instance:

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE emails;
ALTER PUBLICATION supabase_realtime ADD TABLE email_labels;
```

**How to Execute:**
- **Supabase Cloud:** Go to Dashboard → SQL Editor → Paste and Run
- **Local Supabase:** Connect via `psql` and run the commands
- **Via Docker:** `docker exec -it supabase_db_1 psql -U postgres -d postgres`

### 2. Verify Realtime is Enabled

Run this query to confirm:
```sql
SELECT * FROM pg_publication_tables 
WHERE pubname = 'supabase_realtime' 
AND tablename IN ('emails', 'email_labels');

-- Expected result: Should show 2 rows with emails and email_labels
```

### 3. Test in Browser Console

```javascript
// Open DevTools (F12) and paste:
// Should see [Realtime] logs when page loads
console.log('Checking for [Realtime] logs...');

// Classify an email and watch for:
// [Realtime] Email UPDATE received: {...}
```

## How to Test

### Test 1: Check Subscription Connection
1. Open DevTools (F12)
2. Refresh page
3. Look for console logs with `[Realtime]` prefix
4. Should see:
   - `[Realtime] Setting up subscription for user: [UUID]`
   - `[Realtime] Token available: true`
   - `[Realtime] Subscription status: SUBSCRIBED`

### Test 2: Classify Email and Monitor Realtime
1. Keep DevTools Console open
2. Click "Classify" on an email
3. Watch for: `[Realtime] Email UPDATE received: {...}`
4. Check if UI updates automatically with classification
5. If both happen, realtime is working! ✅

### Test 3: Direct Database Update (Advanced)
```javascript
// Update email directly to trigger realtime event
const { data, error } = await supabase
  .from('emails')
  .update({ category_suggestion: 'TEST', updated_at: new Date().toISOString() })
  .eq('id', 'EMAIL_UUID')
  .select();

// Should see [Realtime] logs if subscription is active
```

## Architecture

### Components Involved
1. **Frontend** (Vue 3 + Supabase.js)
   - Creates realtime channel subscription
   - Listens for UPDATE events
   - Reactively updates messages array

2. **Database** (PostgreSQL + Supabase)
   - Stores classification data
   - Publishes changes via realtime
   - Enforces RLS policies

3. **Backend** (Python RAG server)
   - Calls LLM classifier
   - Saves to database via Supabase
   - Database update triggers realtime event

### Security
- **RLS Policies:** Each user only sees/receives events for their own emails
  - Policy: `user_id = (select auth.uid())`
- **JWT Authentication:** Realtime channel authenticated with user's token
- **Channel Filter:** Only events for user's emails: `user_id=eq.${userId}`

## Debugging

### If Realtime Doesn't Work

1. **Check Supabase Realtime Status**
   ```sql
   SELECT * FROM pg_publication_tables 
   WHERE pubname = 'supabase_realtime';
   ```
   - Must include 'emails' and 'email_labels'
   - If missing, run ALTER PUBLICATION commands

2. **Check Browser Console**
   - Look for `[Realtime]` logs
   - Should see subscription status
   - If not, user might not be authenticated

3. **Check Token**
   ```javascript
   console.log('Token:', !!session.value?.access_token);
   ```
   - Must be true
   - If false, log in again

4. **Check RLS Policies**
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'emails';
   ```
   - Should show UPDATE policy with `user_id = (select auth.uid())`

5. **Check Event Filter**
   - Filter syntax: `user_id=eq.${userId}`
   - Make sure `userId` is the UUID from JWT, not email

### Fallback Behavior
- Even if realtime doesn't work, local UI updates immediately
- Classification results show right away
- Data is saved to database
- UI stays in sync through immediate local updates

## Files Modified

| File | Changes |
|------|---------|
| `front/src/components/MailPage.vue` | Added Supabase realtime setup, JWT auth, subscription handler, comprehensive logging |
| `back/schema/emails.sql` | Added ALTER PUBLICATION commands to enable realtime |

## Files Created (Documentation)

| File | Purpose |
|------|---------|
| `REALTIME_IMPLEMENTATION.md` | Detailed implementation guide and summary |
| `REALTIME_DEBUG_GUIDE.md` | Step-by-step debugging instructions |
| `REALTIME_TEST_SCRIPT.md` | Console test commands to verify realtime |

## Next Steps

### For Users
1. ✅ **Run SQL** to enable realtime on Supabase
2. ✅ **Test Console Logs** to verify subscription
3. ✅ **Classify Email** and watch for realtime updates
4. 📝 **Report** if issues - use REALTIME_DEBUG_GUIDE.md

### For Developers
- Monitoring in browser console with `[Realtime]` prefix logs
- Check Supabase dashboard for realtime metrics
- Monitor database query logs for RLS policy enforcement
- Could add error tracking/monitoring for production use

## Performance Considerations

- **Event Throttling:** 10 events/second (configurable)
- **Channel Per User:** Each user has own channel to prevent cross-user events
- **RLS Filtering:** Events filtered by RLS policy before transmission
- **Lazy Unsubscribe:** Cleanup on component unmount

## Security Checklist

- ✅ JWT token authenticated before subscribing
- ✅ RLS policies enforce user-level data isolation
- ✅ Channel filter includes `user_id=eq.${userId}`
- ✅ Realtime events respect RLS policies
- ✅ Token refresh handled automatically

## Known Limitations

1. **Local Realtime Only:** Only works with Supabase local instance (`localhost:8003`)
   - Would need different setup for Supabase Cloud
2. **Polling Fallback:** If realtime disabled, no automatic sync
   - But local updates still work immediately
3. **Browser Tab Sync:** Each tab has independent subscription
   - Tabs don't see each other's classification actions

## Future Enhancements

1. Add reconnection logic for network interruptions
2. Implement offline queueing for classifications
3. Add error notifications for realtime failures
4. Implement cross-tab messaging with localStorage
5. Add metrics/analytics for realtime performance

---

**Status:** ✅ Implementation Complete  
**Testing:** Ready to test after enabling realtime in Supabase  
**Documentation:** Complete with debugging guides and test scripts  

For detailed testing and debugging steps, see:
- `REALTIME_DEBUG_GUIDE.md` - Comprehensive debugging guide
- `REALTIME_TEST_SCRIPT.md` - Console commands to test realtime
