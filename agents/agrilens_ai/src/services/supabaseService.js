// src/services/supabaseService.js
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';

// Replace these with your actual Supabase credentials
const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

const ExpoSecureStoreAdapter = {
  getItem: (key) => SecureStore.getItemAsync(key),
  setItem: (key, value) => SecureStore.setItemAsync(key, value),
  removeItem: (key) => SecureStore.deleteItemAsync(key),
};

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: ExpoSecureStoreAdapter,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});

// Database schema functions
export const plantService = {
  async savePlantScan(plantData) {
    const { data, error } = await supabase
      .from('plant_scans')
      .insert([plantData])
      .select();
    
    if (error) throw error;
    return data[0];
  },

  async getUserScans(userId) {
    const { data, error } = await supabase
      .from('plant_scans')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });
    
    if (error) throw error;
    return data;
  }
};

export const userService = {
  async updateProfile(userId, updates) {
    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select();
    
    if (error) throw error;
    return data[0];
  }
};