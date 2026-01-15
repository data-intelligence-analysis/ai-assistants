// src/screens/HomeScreen.js
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';

const HomeScreen = ({ navigation }) => {
  const { user } = useAuth();
  const { getSubscriptionTier, getRemainingScans } = useSubscription();

  const features = [
    {
      title: 'Plant Identification',
      icon: 'leaf',
      screen: 'Scan',
      description: 'Identify plants and crops instantly',
    },
    {
      title: 'Disease Detection',
      icon: 'bug',
      screen: 'Scan',
      description: 'Detect pests and diseases',
    },
    {
      title: 'Produce Grading',
      icon: 'analytics',
      screen: 'Grading',
      description: 'Grade quality and check prices',
    },
    {
      title: 'AR Forecast',
      icon: 'cube',
      screen: 'AR',
      description: 'See future growth stages',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.welcome}>Welcome back, {user?.email}</Text>
        <Text style={styles.subscription}>
          {getSubscriptionTier().toUpperCase()} Plan • {getRemainingScans()} scans today
        </Text>
      </View>

      <View style={styles.featuresGrid}>
        {features.map((feature, index) => (
          <TouchableOpacity
            key={index}
            style={styles.featureCard}
            onPress={() => navigation.navigate(feature.screen)}
          >
            <Ionicons name={feature.icon} size={32} color="#4CAF50" />
            <Text style={styles.featureTitle}>{feature.title}</Text>
            <Text style={styles.featureDesc}>{feature.description}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.recentSection}>
        <Text style={styles.sectionTitle}>Recent Scans</Text>
        <Text style={styles.emptyText}>No recent scans yet</Text>
        {/* Recent scans list would go here */}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
  },
  welcome: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  subscription: {
    fontSize: 14,
    color: '#666',
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
    justifyContent: 'space-between',
  },
  featureCard: {
    width: '48%',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    alignItems: 'center',
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 10,
    textAlign: 'center',
  },
  featureDesc: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
    textAlign: 'center',
  },
  recentSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontStyle: 'italic',
  },
});

export default HomeScreen;