/**
 * useGeneration.js
 *
 * Custom hook that manages the image generation lifecycle via the real backend API.
 * Handles loading state, error details, and prevents duplicate submissions.
 */

import { useState, useCallback } from 'react';
import { generateImageApi } from '../services/apiService';

export const STATUS = {
  IDLE:    'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR:   'error',
};

export function useGeneration() {
  const [status, setStatus]             = useState(STATUS.IDLE);
  const [result, setResult]             = useState(null);
  const [error, setError]               = useState(null);
  const [errorDetails, setErrorDetails] = useState(null);

  const generate = useCallback(async (params) => {
    // Prevent duplicate in-flight requests
    if (status === STATUS.LOADING) return;

    setStatus(STATUS.LOADING);
    setResult(null);
    setError(null);
    setErrorDetails(null);

    try {
      const data = await generateImageApi(params);
      data.request_params = params;
      setResult(data);
      setStatus(STATUS.SUCCESS);
      return data;
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
      setErrorDetails(err);
      setStatus(STATUS.ERROR);
      return null;
    }
  }, [status]);

  const reset = useCallback(() => {
    setStatus(STATUS.IDLE);
    setResult(null);
    setError(null);
    setErrorDetails(null);
  }, []);

  return { status, result, error, errorDetails, generate, reset };
}
