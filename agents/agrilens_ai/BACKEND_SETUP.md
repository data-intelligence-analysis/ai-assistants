
**docs/BACKEND_SETUP.md**
```markdown
# Backend Setup Guide

## Supabase Configuration

1. Create a new Supabase project at https://supabase.com
2. Get your project URL and anon key from Settings > API
3. Set up database tables by running the SQL below:
4. Enable Row Level Security (RLS) and create policies
5. Set up storage buckets for user uploads

```sql
-- Users table (extends auth.users)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  user_type TEXT DEFAULT 'hobbyist',
  subscription_tier TEXT DEFAULT 'free',
  scan_limit INTEGER DEFAULT 5,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Plant scans table
CREATE TABLE plant_scans (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  image_url TEXT NOT NULL,
  analysis_result JSONB NOT NULL,
  analysis_type TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  product_id TEXT NOT NULL,
  purchase_token TEXT,
  transaction_date TIMESTAMP,
  expires_date TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);
```

