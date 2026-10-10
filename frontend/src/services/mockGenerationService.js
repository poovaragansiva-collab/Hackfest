/**
 * mockGenerationService.js
 *
 * Re-exports production constants from apiService.js to maintain import compatibility.
 * The production user flow uses apiService.js (POST /api/v1/generate).
 */

export {
  USE_CASES,
  TIERS,
  COLOR_OPTIONS,
  REQUIREMENTS_BY_USE_CASE,
  ApiError,
  fetchHealth,
  generateImageApi,
} from './apiService';

