// src/tests/integration/authFlow.test.js
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { useAuth } from '../../hooks/useAuth';
import LoginScreen from '../../screens/LoginScreen';

// Mock the auth hook
jest.mock('../../hooks/useAuth');

describe('Auth Flow Integration', () => {
  test('successful login navigates to home', async () => {
    const mockSignIn = jest.fn().mockResolvedValue({ user: { id: '123' } });
    useAuth.mockReturnValue({
      signIn: mockSignIn,
      loading: false,
    });

    const navigation = { navigate: jest.fn() };
    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={navigation} />
    );

    fireEvent.changeText(getByPlaceholderText('Email'), 'test@example.com');
    fireEvent.changeText(getByPlaceholderText('Password'), 'password123');
    fireEvent.press(getByText('Sign In'));

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(navigation.navigate).toHaveBeenCalledWith('Home');
    });
  });
});