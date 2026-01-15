# README.md

# AgriLens AI - Plant & Crop Identifier

A cross-platform mobile app for plant identification, disease detection, and growth forecasting using AI.

## Features

- 🌱 AI-powered plant identification
- 🔍 Disease and pest detection
- 📊 Produce quality grading
- 🎯 AR growth forecasting
- 📈 Yield prediction
- 💰 Marketplace integration
- 🔄 Offline-first capabilities
- 🎨 Dark mode support

## Tech Stack

- **Frontend**: React Native with Expo
- **Backend**: Supabase (Auth, Database, Storage)
- **AI**: OpenAI Vision API + Google Cloud Vision
- **CI/CD**: GitHub Actions + Fastlane
- **Testing**: Jest, React Native Testing Library, Detox

## Setup

### Prerequisites

- Node.js 18+
- Expo CLI
- iOS: Xcode 15+
- Android: Android Studio

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/agri-lens-ai.git
cd agri-lens-ai
```
2. Install dependencies: `npm install`
3. Set up environment variables: `cp .env.example .env`
4. Start the development server: `expo start`

## Environment Variables

Create a `.env` file with:



## Backend Setup

See `docs/BACKEND_SETUP.md` for Supabase configuration instructions.

## Testing

```bash
# Unit tests
npm test

# Linting
npm run lint
```

## Building for Production
```bash
# Android
eas build --platform android

# iOS
eas build --platform ios
```

## Project Structure

```text
agri-lens-ai.zip/
├── src/                    # React Native source code
├── assets/                 # App icons and images
├── fastlane/              # CI/CD configuration
├── docs/                  # Documentation
├── tests/                 # Test suites
├── .github/workflows/     # GitHub Actions
├── app.json              # Expo configuration
├── package.json          # Dependencies
├── .env.example          # Environment template
└── README.md             # Setup instructions

agri-lens-ai/
├── assets/
├── src/
│   ├── api/
│   ├── components/
│   ├── hooks/
│   ├── navigation/
│   ├── screens/
│   ├── services/
│   ├── styles/
│   ├── tests/
│   └── utils/
├── fastlane/
├── docs/
├── app.json
├── package.json
├── app.config.js
└── README.md
```



## Complete Mobile Package
```bash
agri-lens-ai/
├── src/
│   ├── api/
│   │   ├── aiService.js
│   │   ├── marketService.js
│   │   └── billingService.js
│   ├── components/
│   │   ├── CameraScanner.js
│   │   ├── BarcodeScanner.js
│   │   ├── PlantCard.js
│   │   ├── PlantLog.js
│   │   ├── ARView.js
│   │   └── Dashboard.js
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useAI.js
│   │   └── useSubscription.js
│   ├── navigation/
│   │   ├── AppNavigator.js
│   │   └── AuthNavigator.js
│   ├── screens/
│   │   ├── HomeScreen.js
│   │   ├── ScanScreen.js
│   │   ├── PlantDetailsScreen.js
│   │   ├── MarketplaceScreen.js
│   │   ├── FarmDashboardScreen.js
│   │   └── SettingsScreen.js
│   ├── services/
│   │   ├── aiClient/
│   │   │   ├── openaiClient.js
│   │   │   └── googleVisionClient.js
│   │   ├── storageService.js
│   │   └── supabaseService.js
│   ├── styles/
│   │   ├── colors.js
│   │   ├── typography.js
│   │   └── globalStyles.js
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── aiService.test.js
│   │   │   └── auth.test.js
│   │   ├── integration/
│   │   │   └── authFlow.test.js
│   │   └── e2e/
│   │       └── appFlow.spec.js
│   └── utils/
│       ├── imageUtils.js
│       └── formatters.js
├── assets/
│   ├── icons/
│   │   ├── icon.png
│   │   ├── icon@2x.png
│   │   ├── icon@3x.png
│   │   └── adaptive-icon.png
│   └── images/
│       ├── splash.png
│       └── placeholder-plant.jpg
├── fastlane/
│   ├── Fastfile
│   ├── Appfile
│   └── metadata/
│       ├── android/
│       └── ios/
├── docs/
│   ├── BACKEND_SETUP.md
│   ├── QA_CHECKLIST.md
│   ├── RELEASE_GUIDE.md
│   ├── PRIVACY_POLICY_TEMPLATE.md
│   ├── TERMS_OF_USE_TEMPLATE.md
│   └── DEVELOPER_HANDOFF.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── app.json
├── app.config.js
├── package.json
├── .env.example
├── .eslintrc.js
├── .gitignore
├── babel.config.js
├── jest.config.js
└── README.md
```