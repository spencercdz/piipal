# Supabase Database Setup for PIIPal

This guide will help you set up the database schema and user data management for your PIIPal application.

## 🗄️ Database Schema

The application uses three main tables:

### 1. **user_profiles**
- Stores user profile information
- Automatically created when a user signs up
- Fields: `id`, `user_id`, `email`, `display_name`, `avatar_url`, `created_at`, `updated_at`

### 2. **processed_files**
- Tracks all files processed by users
- Stores metadata about original and processed files
- Fields: `id`, `user_id`, `original_filename`, `processed_filename`, `file_type`, `file_size`, `processing_status`, `created_at`, `updated_at`

### 3. **user_preferences**
- Stores user settings and preferences
- Automatically created with default values
- Fields: `id`, `user_id`, `auto_process`, `email_notifications`, `theme`, `language`, `created_at`, `updated_at`

## 🚀 Setup Instructions

### Step 1: Create Database Tables

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `SUPABASE_SCHEMA.sql`
4. Click **Run** to execute the schema

### Step 2: Verify Tables Created

In the **Table Editor**, you should see:
- `user_profiles`
- `processed_files` 
- `user_preferences`

### Step 3: Test Row Level Security

The schema includes Row Level Security (RLS) policies that ensure:
- Users can only see their own data
- Users can only modify their own data
- Automatic profile/preferences creation on signup

## 📊 Features Included

### **User Data Management**
- ✅ Automatic profile creation on signup
- ✅ User preferences with defaults
- ✅ Profile updates (display name, avatar)
- ✅ Preference management (theme, notifications, etc.)

### **File Tracking**
- ✅ Save processed file metadata
- ✅ Track processing status
- ✅ File history per user
- ✅ File deletion

### **Analytics**
- ✅ User statistics (total files, success rate, etc.)
- ✅ Monthly processing counts
- ✅ File type breakdowns

## 🔧 Usage Examples

### **Using the useUserData Hook**

```tsx
import { useUserData } from '@/hooks/useUserData'

function MyComponent() {
  const { 
    profile, 
    preferences, 
    processedFiles, 
    stats, 
    loading,
    updateProfile,
    updatePreferences,
    addProcessedFile 
  } = useUserData()

  // Update user profile
  const handleUpdateProfile = async () => {
    await updateProfile({ display_name: 'New Name' })
  }

  // Update preferences
  const handleUpdatePreferences = async () => {
    await updatePreferences({ theme: 'light' })
  }

  // Add a processed file
  const handleAddFile = async () => {
    await addProcessedFile({
      original_filename: 'video.mp4',
      processed_filename: 'censored_video.mp4',
      file_type: 'video',
      file_size: 1024000,
      processing_status: 'completed'
    })
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1>Welcome, {profile?.display_name || profile?.email}</h1>
      <p>Files processed: {stats?.total_files}</p>
      <p>Theme: {preferences?.theme}</p>
    </div>
  )
}
```

### **Direct Database Functions**

```tsx
import { 
  getUserProfile, 
  updateUserProfile,
  getUserProcessedFiles,
  saveProcessedFile 
} from '@/lib/supabase-database'

// Get user profile
const { data: profile } = await getUserProfile(userId)

// Update profile
const { data: updatedProfile } = await updateUserProfile(userId, {
  display_name: 'New Name'
})

// Get user's files
const { data: files } = await getUserProcessedFiles(userId)

// Save processed file
const { data: savedFile } = await saveProcessedFile({
  user_id: userId,
  original_filename: 'original.jpg',
  processed_filename: 'censored.jpg',
  file_type: 'image',
  file_size: 500000,
  processing_status: 'completed'
})
```

## 🔒 Security Features

### **Row Level Security (RLS)**
- All tables have RLS enabled
- Users can only access their own data
- Automatic policies prevent data leakage

### **Automatic Triggers**
- Profile and preferences created on signup
- `updated_at` timestamps automatically maintained
- Data integrity enforced at database level

## 📈 Analytics Available

The `getUserStats` function provides:
- Total files processed
- Completed vs failed files
- Images vs videos processed
- Files processed this month
- Success rate calculations

## 🎯 Next Steps

1. **Run the schema** in your Supabase SQL Editor
2. **Test user registration** - profiles should auto-create
3. **Integrate file tracking** in your processing workflow
4. **Add user preferences UI** for settings management
5. **Implement analytics dashboard** using the stats functions

## 🐛 Troubleshooting

### **Profile not created on signup**
- Check if the trigger function exists
- Verify RLS policies are active
- Check Supabase logs for errors

### **Permission denied errors**
- Ensure RLS policies are correctly set
- Verify user is authenticated
- Check if user_id matches auth.uid()

### **Data not loading**
- Check network requests in browser dev tools
- Verify Supabase URL and keys are correct
- Check Supabase logs for API errors
