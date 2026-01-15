import { openAIClient } from '../../services/aiClient/openaiClient';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    post: jest.fn(),
  })),
}));

describe('OpenAIClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('getPromptForAnalysisType returns correct prompts', () => {
    expect(openAIClient.getPromptForAnalysisType('identification')).toContain('Identify this plant');
    expect(openAIClient.getPromptForAnalysisType('disease')).toContain('Analyze this plant');
    expect(openAIClient.getPromptForAnalysisType('grading')).toContain('Grade this produce');
  });

  test('parseAIResponse handles JSON and fallback', () => {
    const jsonResponse = '{"species": "Rose", "confidence": 0.95}';
    const textResponse = 'This is a rose plant';

    expect(openAIClient.parseAIResponse(jsonResponse)).toEqual({
      species: 'Rose',
      confidence: 0.95,
    });

    expect(openAIClient.parseAIResponse(textResponse)).toEqual({
      rawResponse: textResponse,
    });
  });
});