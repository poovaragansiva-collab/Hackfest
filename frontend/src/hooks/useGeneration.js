/**
 * useGeneration.js
 *
 * Custom hook that manages the image generation lifecycle.
 * Completely decoupled from the service implementation — swap
 * the service import when the real backend is ready.
 */

import { useState, useCallback } from 'react';
import { generateImage } from '../services/mockGenerationService';

export const STATUS = {
  IDLE:    'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR:   'error',
};

export function useGeneration() {
  const [status, setStatus]   = useState(STATUS.IDLE);
  const [result, setResult]   = useState(null);
  const [error,  setError]    = useState(null);

  const generate = useCallback(async (params) => {
    setStatus(STATUS.LOADING);
    setResult(null);
    setError(null);

    try {
      const data = await generateImage(params);
      setResult(data);
      setStatus(STATUS.SUCCESS);
    } catch (err) {
      setError(err.message ?? 'Something went wrong. Please try again.');
      setStatus(STATUS.ERROR);
    }
  }, []);

  const reset = useCallback(() => {
    setStatus(STATUS.IDLE);
    setResult(null);
    setError(null);
  }, []);

  return { status, result, error, generate, reset };
}
