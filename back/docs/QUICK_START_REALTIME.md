# 🚀 Quick Start - Enable Realtime in 2 Minutes

## TL;DR - Just Copy & Paste This

### Step 1: Run This SQL Command

Go to your Supabase instance and run:

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE emails;
ALTER PUBLICATION supabase_realtime ADD TABLE email_labels;
```

**Where to run it:**

1. **Supabase Cloud Dashboard**
   - Go to: https://app.supabase.com
   - Select your project
   - Click "SQL Editor" on the left
   - Click "New query"
   - Paste the SQL above
   - Click "Run"

2. **Local Supabase (Docker)**
   ```bash
   docker exec -it supabase_db psql -U postgres -d postgres
   # Then paste the SQL above
   ```

3. **Local Supabase (psql)**
   ```bash
   psql postgresql://postgres:postgres@localhost:5432/postgres
   # Then paste the SQL above
   ```

### Step 2: Test in Browser Console

1. Open browser DevTools: **F12**
2. Go to **Console** tab
3. Refresh the page
4. Look for logs starting with `[Realtime]`
5. Should see: `Subscription status: SUBSCRIBED`

### Step 3: Test Classification

1. Click **"Classify"** on any email
2. Watch browser console for: `Email UPDATE received`
3. Check if UI updates with classification

### Done! 🎉

If you see the `[Realtime]` logs and email updates appear, realtime is working!

---

## If It Doesn't Work

### Verify Realtime is Enabled

Run this query to check:
```sql
SELECT tablename FROM pg_publication_tables 
WHERE pubname = 'supabase_realtime';
```

**Expected output:** Should list `emails` and `email_labels`

If not listed:
1. Run the ALTER PUBLICATION commands above again
2. Make sure there are no SQL errors

### Check Browser Console

Look for one of these issues:

❌ **No `[Realtime]` logs at all**
- User might not be logged in
- Or realtime not enabled on table

❌ **Subscription status is "CHANNEL_ERROR"**
- Realtime not enabled on emails table
- Run the SQL commands again

❌ **Token available: false**
- User not authenticated
- Log in first before testing

❌ **UPDATE events received but UI doesn't change**
- Check email IDs are matching
- Open DevTools and check console logs

---

## More Information

For detailed help, see:
- 📖 `REALTIME_COMPLETE_SOLUTION.md` - Full technical documentation
- 🔧 `REALTIME_DEBUG_GUIDE.md` - Detailed troubleshooting
- 🧪 `REALTIME_TEST_SCRIPT.md` - Console test commands

---

## The 3 Things That Must Happen

1. ✅ **Realtime enabled in Supabase** (ALTER PUBLICATION command)
2. ✅ **User is authenticated** (logged in with valid JWT)
3. ✅ **Classification triggers database update** (saves to emails table)

Once all three happen, the UI should update automatically! 🚀

---

## Video Summary

What's happening:

1. You classify an email → Frontend sends to backend
2. Backend saves to database → PostgreSQL triggers realtime event
3. Supabase publishes event → Frontend subscription receives it
4. Frontend updates UI → You see classification appear instantly

That's it! Just enable realtime and it works.

---

**Need Help?**
- Check `REALTIME_DEBUG_GUIDE.md` for step-by-step debugging
- Run test commands from `REALTIME_TEST_SCRIPT.md` in console
- Look for `[Realtime]` logs to see what's happening
