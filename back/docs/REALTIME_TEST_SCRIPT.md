# Quick Test Script for Supabase Realtime

Run these commands in your browser console (F12) to test if realtime is working:

## Test 1: Check Session
```javascript
// From MailPage component
const session = useAuth().session;
console.log('Session:', session.value);
console.log('User ID:', session.value?.user?.id);
console.log('Access Token:', !!session.value?.access_token);
```

## Test 2: Check Supabase Client
```javascript
// Test if Supabase client is properly set up
const supabase = createClient(
  'http://localhost:8003',
  'eyJhbGc...' // your VITE_SUPABASE_ANON_KEY
);
console.log('Supabase client created');
```

## Test 3: Direct Subscription Test
```javascript
// Test basic realtime connectivity (no auth)
const testChannel = supabase
  .channel('test-realtime')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'emails' },
    payload => console.log('🔔 REALTIME EVENT:', payload)
  )
  .subscribe(status => {
    console.log('📡 Subscription status:', status);
    if (status === 'SUBSCRIBED') {
      console.log('✅ Realtime is connected!');
    } else if (status === 'CHANNEL_ERROR') {
      console.error('❌ Realtime connection error - check if table has realtime enabled');
    }
  });

// Unsubscribe after 30 seconds
setTimeout(() => {
  testChannel.unsubscribe();
}, 30000);
```

## Test 4: Check if Emails Table Has Realtime
```javascript
// Query to check if realtime is enabled on emails table
// Run in Supabase SQL Editor:

SELECT * FROM pg_publication_tables 
WHERE pubname = 'supabase_realtime' 
AND schemaname = 'public';

-- Should show 'emails' in the tablename column
```

## Test 5: Manual Database Update (Trigger Realtime Event)
```javascript
// Update an email classification directly to trigger realtime event
const response = await supabase
  .from('emails')
  .update({
    category_suggestion: 'TEST_UPDATE',
    classification_reason: 'Manual test from console',
    updated_at: new Date().toISOString()
  })
  .eq('id', 'YOUR_EMAIL_UUID_HERE')  // Replace with actual email UUID
  .select();

console.log('Update response:', response);
// This should trigger [Realtime] UPDATE events if realtime is enabled
```

## Test 6: Monitor Console for Realtime Logs
```javascript
// These logs should appear when realtime is working:
// [Realtime] Setting up subscription for user: [UUID]
// [Realtime] Token available: true
// [Realtime] Creating channel: emails:[UUID]
// [Realtime] Subscription status: SUBSCRIBED
// [Realtime] Email UPDATE received: {...}

// If you see these, realtime is working! 🎉
```

## Expected Console Output When Working

```
[Realtime] User authenticated, setting up subscription
[Realtime] Setting up subscription for user: 12345678-1234-1234-1234-123456789012
[Realtime] Supabase URL: http://localhost:8003
[Realtime] Creating channel: emails:12345678-1234-1234-1234-123456789012
[Realtime] Token available: true
[Realtime] Auth session set
[Realtime] Subscription status: SUBSCRIBED
```

When you classify an email:
```
Classifying email: 87654321-4321-4321-4321-210987654321
[Realtime] Email UPDATE received: { new: {...}, old: {...}, ... }
[Realtime] Updated email data: { id: '...', category_suggestion: '...', ... }
[Realtime] Found email at index: 0
[Realtime] Updated email successfully: 87654321-4321-4321-4321-210987654321
```

## Troubleshooting

**Issue: "CHANNEL_ERROR" in subscription status**
```javascript
// Realtime is not enabled on the table
// Run in Supabase SQL Editor:
ALTER PUBLICATION supabase_realtime ADD TABLE emails;
```

**Issue: No subscription logs appearing**
```javascript
// Check if user is authenticated
const { session } = useAuth();
console.log('Is authenticated:', !!session.value?.access_token);

// If false, log in first before testing
```

**Issue: Token is not being set**
```javascript
// Manually set the token for testing:
const token = session.value?.access_token;
const refreshToken = session.value?.refresh_token;

await supabase.auth.setSession({
  access_token: token,
  refresh_token: refreshToken || '',
});
```

**Issue: Update event not received**
```javascript
// Check RLS policies are correct:
SELECT * FROM pg_policies WHERE tablename = 'emails';

// Should see:
// - Users can view own emails
// - Users can update own emails
// All using: user_id = (select auth.uid())
```

---

**Success Indicators:**
- ✅ Subscription status is "SUBSCRIBED"
- ✅ Token is "true"
- ✅ Email UPDATE events received after classification
- ✅ UI updates automatically with new classification

**If all these are working, realtime is fully functional! 🚀**
