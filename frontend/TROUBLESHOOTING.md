# Troubleshooting Loading Issues

## 🐛 App Stuck on Loading

If your app is stuck on the loading screen, here are the most common causes and solutions:

### **1. Check Environment Variables**

Make sure your `.env.local` file has the correct Supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

**To verify:**
- Check the debug info in the bottom-right corner (development mode only)
- Look for "Supabase URL: set" and "Supabase Key: set"

### **2. Supabase Project Status**

**Check if your Supabase project is active:**
- Go to your Supabase dashboard
- Make sure the project is not paused
- Verify the project URL matches your environment variable

### **3. Database Tables Not Created**

**If you haven't run the database schema yet:**
1. Go to Supabase → SQL Editor
2. Copy and paste the contents of `SUPABASE_SCHEMA.sql`
3. Click "Run" to create the tables

**If tables exist but there are errors:**
- Check the Supabase logs for any database errors
- Verify Row Level Security policies are working

### **4. Network Issues**

**Check browser console for errors:**
- Open Developer Tools (F12)
- Look for network errors or failed requests
- Check if Supabase requests are timing out

### **5. Authentication Flow Issues**

**Common problems:**
- Invalid Supabase credentials
- CORS issues (shouldn't happen with Supabase)
- Session initialization failing

### **6. Quick Fixes**

**Restart the development server:**
```bash
# Stop the current server (Ctrl+C)
npm run dev
```

**Clear browser cache:**
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- Or open in incognito/private mode

**Check Supabase logs:**
- Go to Supabase → Logs
- Look for any authentication or database errors

### **7. Debug Information**

The debug component shows:
- Loading state
- Authentication status
- Environment variables status
- User information (if authenticated)

### **8. Fallback Solution**

If nothing works, temporarily disable the database initialization:

```tsx
// In AuthContext.tsx, comment out the initializeUserData calls
// This will allow the app to load without trying to create profiles
```

### **9. Common Error Messages**

**"Invalid API key":**
- Check your Supabase anon key
- Make sure it's the "anon public" key, not the service role key

**"Failed to fetch":**
- Check your internet connection
- Verify Supabase project is not paused
- Check if there are any firewall restrictions

**"Row Level Security policy violation":**
- Run the database schema to create proper RLS policies
- Or temporarily disable RLS for testing

### **10. Still Having Issues?**

1. **Check the browser console** for specific error messages
2. **Check Supabase logs** in your project dashboard
3. **Verify environment variables** are correctly set
4. **Test Supabase connection** by creating a simple test query
5. **Try in incognito mode** to rule out browser cache issues

The debug component should help identify exactly what's causing the loading issue!
