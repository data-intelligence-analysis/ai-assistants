# AgriLens AI Developer Handoff Guide

## Team Roles & Responsibilities

### Frontend Team
- React Native development
- UI/UX implementation
- Cross-platform compatibility
- App store deployment

### Backend Team
- Supabase configuration
- Database management
- API integration
- AI service coordination

### DevOps Team
- CI/CD pipeline management
- App store publishing
- Monitoring and analytics
- Security compliance

## Environment Setup

### Required Accounts
1. **Apple Developer Account** ($99/year)
2. **Google Play Developer Account** ($25 one-time)
3. **Supabase Account** (Free tier available)
4. **OpenAI API Account** (Pay-as-you-go)
5. **Google Cloud Vision Account** (Optional)

### API Keys Rotation Schedule
- Supabase keys: Rotate every 90 days
- OpenAI key: Rotate every 180 days
- App Store Connect API key: Rotate annually

## Critical Integration Points

### 1. Supabase Configuration
- Enable email authentication
- Set up database tables (see schema.sql)
- Configure Row Level Security (RLS)
- Set up storage buckets for images

### 2. AI Service Integration
- OpenAI Vision API for plant identification
- Google Cloud Vision for fallback analysis
- Local model caching for offline use

### 3. In-App Purchases
- Configure products in App Store Connect
- Set up products in Google Play Console
- Implement purchase validation backend

## Monitoring & Analytics

### Essential Metrics
- Daily active users (DAU)
- Scan success rate
- Subscription conversion rate
- Crash-free sessions

### Tools Setup
- Firebase Crashlytics for error monitoring
- Google Analytics for user behavior
- RevenueCat for subscription analytics

## Release Process

### Staging Releases
1. Test on internal tracks
2. Validate all subscription flows
3. Test offline functionality
4. Verify AR features

### Production Releases
1. Submit to Apple App Store (5-7 day review)
2. Submit to Google Play (2-3 day review)
3. Monitor initial crash reports
4. Gather user feedback

## Support Resources

### Documentation
- API documentation: /docs/api.md
- Database schema: /docs/database.md
- Testing guide: /docs/testing.md

### Contact Points
- Technical support: dev@agrilensai.com
- App store issues: publish@agrilensai.com
- Security concerns: security@agrilensai.com