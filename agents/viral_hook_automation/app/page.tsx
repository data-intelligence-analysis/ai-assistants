"use client"
import { useState } from 'react';

const ViralReelAutomation = () => {
  const [activeTab, setActiveTab] = useState('generate');
  const [searchTerm, setSearchTerm] = useState('fitness');
  const [ideas, setIdeas] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [automationSettings, setAutomationSettings] = useState({
    frequency: 'daily',
    time: '09:00',
    platforms: ['instagram', 'tiktok'],
    minViralScore: 100000
  });

  // Mock viral reel data structure
  const mockViralData = {
    fitness: [
      {
        id: 1,
        title: "5-Minute HIIT That Burns Fat All Day",
        hook: "POV: You only have 5 minutes but want maximum results",
        platform: "Instagram",
        views: "2.3M",
        engagement: "8.4%",
        viralScore: 234000,
        transcript: "Start with 30 seconds jumping jacks, then 30 seconds mountain climbers...",
        url: "mock-url-1"
      },
      {
        id: 2,
        title: "Why Your Core Workouts Aren't Working",
        hook: "Stop doing crunches if you want real abs",
        platform: "TikTok",
        views: "1.8M",
        engagement: "12.1%",
        viralScore: 187000,
        transcript: "The problem with crunches is they only work one muscle...",
        url: "mock-url-2"
      },
      {
        id: 3,
        title: "Pre-Workout Food That Changed Everything",
        hook: "I ate this before every workout for 30 days",
        platform: "Instagram",
        views: "1.5M",
        engagement: "9.7%",
        viralScore: 156000,
        transcript: "Banana with almond butter 30 minutes before training...",
        url: "mock-url-3"
      }
    ]
  };

  const generateViralIdeas = () => {
    if (!searchTerm.trim()) {
      alert('Please enter a niche to analyze!');
      return;
    }
    
    setIsLoading(true);
    
    setTimeout(() => {
      const viralReels = mockViralData[searchTerm.toLowerCase()] || generateGenericViralData(searchTerm);
      setIdeas(viralReels);
      setIsLoading(false);
    }, 2000);
  };

  const generateGenericViralData = (topic) => {
    return [
      {
        id: 1,
        title: `${topic} Mistake Everyone Makes`,
        hook: `Stop doing ${topic} wrong - here's the right way`,
        platform: "TikTok",
        views: "1.2M",
        engagement: "11.3%",
        viralScore: 142000,
        transcript: `Most people approach ${topic} completely wrong...`,
        url: "mock-url-generic-1"
      },
      {
        id: 2,
        title: `${topic} Hack That Went Viral`,
        hook: `This ${topic} trick blew everyone's mind`,
        platform: "Instagram",
        views: "890K",
        engagement: "15.2%",
        viralScore: 98000,
        transcript: `I discovered this ${topic} method by accident...`,
        url: "mock-url-generic-2"
      },
      {
        id: 3,
        title: `${topic} Transformation in 30 Days`,
        hook: `Day 1 vs Day 30 of ${topic} - incredible results`,
        platform: "TikTok",
        views: "2.1M",
        engagement: "13.8%",
        viralScore: 201000,
        transcript: `Starting this ${topic} journey changed everything...`,
        url: "mock-url-generic-3"
      }
    ];
  };

  const connectToGoogle = () => {
    setIsLoading(true);
    // Simulate OAuth flow
    setTimeout(() => {
      setIsConnected(true);
      setIsLoading(false);
      alert('Successfully connected to Google Calendar!');
    }, 2000);
  };

  const scheduleReminders = () => {
    if (!isConnected) {
      alert('Please connect to Google Calendar first!');
      return;
    }
    
    alert(`Scheduled ${automationSettings.frequency} reminders at ${automationSettings.time} for your viral reel ideas!`);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      generateViralIdeas();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Viral Reel Automation</h1>
          <p className="text-white/80">AI-powered viral content discovery & automation</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-full p-1 flex space-x-1">
            <button
              onClick={() => setActiveTab('generate')}
              className={`px-6 py-2 rounded-full transition-all ${
                activeTab === 'generate' 
                  ? 'bg-white text-purple-600 font-semibold' 
                  : 'text-white hover:bg-white/20'
              }`}
            >
              Viral Discovery
            </button>
            <button
              onClick={() => setActiveTab('connect')}
              className={`px-6 py-2 rounded-full transition-all ${
                activeTab === 'connect' 
                  ? 'bg-white text-purple-600 font-semibold' 
                  : 'text-white hover:bg-white/20'
              }`}
            >
              Automation Setup
            </button>
          </div>
        </div>

        {/* Content Sections */}
        {activeTab === 'generate' && (
          <div>
            {/* Search Section */}
            <div className="mb-8 space-y-4">
              <div className="relative max-w-2xl mx-auto">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter your niche (e.g., fitness, cooking, business)"
                  className="w-full px-6 py-4 text-white placeholder-white/70 bg-white/20 backdrop-blur-sm border border-white/30 rounded-full text-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50"
                />
              </div>
              
              <div className="flex justify-center">
                <button
                  onClick={generateViralIdeas}
                  disabled={isLoading}
                  className="px-8 py-3 bg-white/30 backdrop-blur-sm border border-white/40 rounded-full text-white font-medium hover:bg-white/40 transition-all duration-200 flex items-center space-x-2 disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Analyzing Viral Content...</span>
                    </>
                  ) : (
                    <>
                      <span>🔥 Find Viral Reels</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Viral Reels Results */}
            {ideas.length > 0 && (
              <div className="grid gap-6 max-h-96 overflow-y-auto">
                {ideas.map((reel) => (
                  <div
                    key={reel.id}
                    className="bg-white/15 backdrop-blur-sm border border-white/30 rounded-2xl p-6 hover:bg-white/20 transition-all duration-200"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-white text-xl font-semibold mb-2">
                          {reel.title}
                        </h3>
                        <p className="text-white/90 mb-3 italic">
                          "{reel.hook}"
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 bg-white/20 rounded-full px-3 py-1">
                        <span className="text-white text-sm">{reel.platform}</span>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-white font-bold text-lg">{reel.views}</div>
                        <div className="text-white/60 text-sm">Views</div>
                      </div>
                      <div className="text-center">
                        <div className="text-white font-bold text-lg">{reel.engagement}</div>
                        <div className="text-white/60 text-sm">Engagement</div>
                      </div>
                      <div className="text-center">
                        <div className="text-white font-bold text-lg">{reel.viralScore.toLocaleString()}</div>
                        <div className="text-white/60 text-sm">Viral Score</div>
                      </div>
                    </div>

                    {/* Transcript */}
                    <div className="bg-white/10 rounded-lg p-4 mb-4">
                      <h4 className="text-white font-medium mb-2">Hook Transcript:</h4>
                      <p className="text-white/80 text-sm">{reel.transcript}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-between items-center">
                      <button className="text-white/70 hover:text-white transition-colors">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h8a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                        </svg>
                      </button>
                      <button className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg transition-colors text-sm">
                        Copy Hook
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {ideas.length === 0 && !isLoading && (
              <div className="text-center text-white/80 py-12">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p className="text-lg">Enter your niche to discover viral reels and extract proven hooks!</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'connect' && (
          <div className="max-w-2xl mx-auto">
            {/* Google Calendar Connection */}
            <div className="bg-white/15 backdrop-blur-sm border border-white/30 rounded-2xl p-8 mb-6">
              <h3 className="text-white text-2xl font-semibold mb-4 text-center">
                🗓️ Google Calendar Integration
              </h3>
              
              {!isConnected ? (
                <div className="text-center">
                  <p className="text-white/80 mb-6">
                    Connect your Google account to automatically schedule viral reel ideas as calendar reminders
                  </p>
                  <button
                    onClick={connectToGoogle}
                    disabled={isLoading}
                    className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-3 px-8 rounded-full flex items-center space-x-3 mx-auto transition-all disabled:opacity-50"
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-gray-800/30 border-t-gray-800 rounded-full animate-spin"></div>
                    ) : (
                      <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                    )}
                    <span>{isLoading ? 'Connecting...' : 'Connect Google Account'}</span>
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <div className="mb-4">
                    <span className="bg-green-500 text-white px-4 py-2 rounded-full text-sm">
                      ✅ Connected to Google Calendar
                    </span>
                  </div>
                  <p className="text-white/80">Ready to schedule automated viral reel reminders!</p>
                </div>
              )}
            </div>

            {/* Automation Settings */}
            <div className="bg-white/15 backdrop-blur-sm border border-white/30 rounded-2xl p-8">
              <h3 className="text-white text-2xl font-semibold mb-6 text-center">
                ⚙️ Automation Settings
              </h3>

              <div className="space-y-6">
                {/* Frequency */}
                <div>
                  <label className="block text-white font-medium mb-2">Reminder Frequency</label>
                  <select
                    value={automationSettings.frequency}
                    onChange={(e) => setAutomationSettings({...automationSettings, frequency: e.target.value})}
                    className="w-full p-3 bg-white/20 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/50"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                  </select>
                </div>

                {/* Time */}
                <div>
                  <label className="block text-white font-medium mb-2">Reminder Time</label>
                  <input
                    type="time"
                    value={automationSettings.time}
                    onChange={(e) => setAutomationSettings({...automationSettings, time: e.target.value})}
                    className="w-full p-3 bg-white/20 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/50"
                  />
                </div>

                {/* Minimum Viral Score */}
                <div>
                  <label className="block text-white font-medium mb-2">Minimum Viral Score</label>
                  <input
                    type="number"
                    value={automationSettings.minViralScore}
                    onChange={(e) => setAutomationSettings({...automationSettings, minViralScore: parseInt(e.target.value)})}
                    className="w-full p-3 bg-white/20 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="100000"
                  />
                  <p className="text-white/60 text-sm mt-1">Only include reels with this minimum viral score</p>
                </div>

                {/* Platforms */}
                <div>
                  <label className="block text-white font-medium mb-2">Monitor Platforms</label>
                  <div className="space-y-2">
                    {['instagram', 'tiktok', 'youtube'].map(platform => (
                      <label key={platform} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={automationSettings.platforms.includes(platform)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setAutomationSettings({
                                ...automationSettings,
                                platforms: [...automationSettings.platforms, platform]
                              });
                            } else {
                              setAutomationSettings({
                                ...automationSettings,
                                platforms: automationSettings.platforms.filter(p => p !== platform)
                              });
                            }
                          }}
                          className="rounded"
                        />
                        <span className="text-white capitalize">{platform}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Schedule Button */}
                <button
                  onClick={scheduleReminders}
                  className="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all"
                >
                  🚀 Schedule Automated Reminders
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViralReelAutomation;