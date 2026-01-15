// src/services/aiClient/openaiClient.js
import axios from 'axios';

const OPENAI_API_KEY = process.env.EXPO_PUBLIC_OPENAI_API_KEY;
const OPENAI_BASE_URL = 'https://api.openai.com/v1';

class OpenAIClient {
  constructor() {
    this.client = axios.create({
      baseURL: OPENAI_BASE_URL,
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async analyzePlantImage(imageUri, analysisType = 'identification') {
    try {
      // Convert image to base64
      const base64Image = await this.imageToBase64(imageUri);
      
      const prompt = this.getPromptForAnalysisType(analysisType);
      
      const response = await this.client.post('/chat/completions', {
        model: 'gpt-4-vision-preview',
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: prompt },
              {
                type: 'image_url',
                image_url: {
                  url: `data:image/jpeg;base64,${base64Image}`,
                },
              },
            ],
          },
        ],
        max_tokens: 1000,
      });

      return this.parseAIResponse(response.data.choices[0].message.content);
    } catch (error) {
      console.error('OpenAI API Error:', error);
      throw new Error('Failed to analyze image');
    }
  }

  getPromptForAnalysisType(type) {
    const prompts = {
      identification: `Identify this plant species and variety. Provide common name, scientific name, family, and basic care information.`,
      disease: `Analyze this plant for diseases, pests, or nutrient deficiencies. Identify any issues and provide treatment recommendations.`,
      grading: `Grade this produce for quality. Assess ripeness, quality grade (export, premium, standard), and provide market price estimation.`,
    };
    return prompts[type] || prompts.identification;
  }

  async imageToBase64(uri) {
    // Implementation for converting image to base64
    // This would use expo-file-system in a real implementation
    return 'base64_placeholder';
  }

  parseAIResponse(response) {
    // Parse the AI response into structured data
    try {
      return JSON.parse(response);
    } catch {
      return { rawResponse: response };
    }
  }
}

export const openAIClient = new OpenAIClient();