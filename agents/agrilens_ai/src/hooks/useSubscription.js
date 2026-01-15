// src/hooks/useSubscription.js
import { useState, useEffect } from 'react';
import { supabase } from '../services/supabaseService';
import * as InAppPurchases from 'expo-in-app-purchases';

const SUBSCRIPTION_TIERS = {
  FREE: 'free',
  HOBBYIST: 'hobbyist',
  PRO: 'pro',
};

const SUBSCRIPTION_LIMITS = {
  [SUBSCRIPTION_TIERS.FREE]: {
    dailyScans: 5,
    features: ['basic_scan', 'plant_log'],
  },
  [SUBSCRIPTION_TIERS.HOBBYIST]: {
    dailyScans: 50,
    features: ['basic_scan', 'disease_detection', 'plant_log', 'care_reminders'],
  },
  [SUBSCRIPTION_TIERS.PRO]: {
    dailyScans: Infinity,
    features: ['all_features', 'bulk_upload', 'ar_forecasting', 'export_reports'],
  },
};

export const useSubscription = () => {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  const initIAP = async () => {
    try {
      await InAppPurchases.connectAsync();
      
      // Set IAP listeners
      InAppPurchases.setPurchaseListener(({ responseCode, results, errorCode }) => {
        if (responseCode === InAppPurchases.IAPResponseCode.OK) {
          results.forEach(async (purchase) => {
            if (purchase.acknowledged) return;
            
            // Verify purchase with backend
            await verifyPurchase(purchase);
            await InAppPurchases.finishTransactionAsync(purchase, true);
          });
        }
      });
    } catch (error) {
      console.error('IAP initialization failed:', error);
    }
  };

  const verifyPurchase = async (purchase) => {
    // Verify purchase with your backend
    const { data, error } = await supabase
      .from('subscriptions')
      .upsert({
        user_id: currentUser.id,
        product_id: purchase.productId,
        purchase_token: purchase.purchaseToken,
        transaction_date: new Date(purchase.transactionDate),
        expires_date: new Date(purchase.expiresDate),
      });

    if (!error) {
      await refreshSubscription(currentUser.id);
    }
  };

  const refreshSubscription = async (userId) => {
    const { data, error } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .eq('is_active', true)
      .single();

    if (!error && data) {
      setSubscription(data);
    } else {
      setSubscription({ tier: SUBSCRIPTION_TIERS.FREE });
    }
    setLoading(false);
  };

  const getSubscriptionTier = () => {
    return subscription?.tier || SUBSCRIPTION_TIERS.FREE;
  };

  const canUseFeature = (feature) => {
    const tier = getSubscriptionTier();
    return SUBSCRIPTION_LIMITS[tier]?.features.includes(feature) || false;
  };

  const getRemainingScans = () => {
    const tier = getSubscriptionTier();
    const limit = SUBSCRIPTION_LIMITS[tier]?.dailyScans;
    return limit === Infinity ? 'unlimited' : limit;
  };

  return {
    subscription,
    loading,
    refreshSubscription,
    getSubscriptionTier,
    canUseFeature,
    getRemainingScans,
    initIAP,
  };
};