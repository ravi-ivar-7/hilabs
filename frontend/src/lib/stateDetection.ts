/**
 * Utility functions for detecting state from filename
 */

export interface StateDetectionResult {
  state: 'TN' | 'WA' | null;
  error?: string;
}

/**
 * Detects state from filename by looking for TN or WA patterns
 * @param filename - The filename to analyze
 * @returns StateDetectionResult with detected state or error
 */
export function detectStateFromFilename(filename: string): StateDetectionResult {
  // Remove file extension and convert to uppercase for matching
  const nameWithoutExt = filename.replace(/\.[^/.]+$/, '').toUpperCase();
  
  // Check for TN patterns
  const tnPatterns = [
    /\bTN\b/,           // Exact TN match
    /TENNESSEE/,        // Full state name
    /\bTN[-_]/,         // TN followed by dash or underscore
    /[-_]TN\b/,         // TN preceded by dash or underscore
    /[-_]TN[-_]/        // TN surrounded by dashes or underscores
  ];
  
  // Check for WA patterns
  const waPatterns = [
    /\bWA\b/,           // Exact WA match
    /WASHINGTON/,       // Full state name
    /\bWA[-_]/,         // WA followed by dash or underscore
    /[-_]WA\b/,         // WA preceded by dash or underscore
    /[-_]WA[-_]/        // WA surrounded by dashes or underscores
  ];
  
  const hasTN = tnPatterns.some(pattern => pattern.test(nameWithoutExt));
  const hasWA = waPatterns.some(pattern => pattern.test(nameWithoutExt));
  
  // Check for conflicts (both states detected)
  if (hasTN && hasWA) {
    return {
      state: null,
      error: `Filename "${filename}" contains both TN and WA identifiers. Please use a filename that clearly indicates only one state.`
    };
  }
  
  // Return detected state
  if (hasTN) {
    return { state: 'TN' };
  }
  
  if (hasWA) {
    return { state: 'WA' };
  }
  
  // No state detected
  return {
    state: null,
    error: `Filename "${filename}" must contain "TN" or "WA" to indicate the contract state. Please rename your file to include the state identifier (e.g., "contract_TN.pdf" or "contract_WA.pdf").`
  };
}

/**
 * Validates multiple files for state detection
 * @param files - Array of files to validate
 * @returns Array of results with filename and detection result
 */
export function validateFilesForState(files: File[]): Array<{ file: File; result: StateDetectionResult }> {
  return files.map(file => ({
    file,
    result: detectStateFromFilename(file.name)
  }));
}
