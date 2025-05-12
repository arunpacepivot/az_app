export const apiService = {
  /**
   * Test connectivity with backend
   * @param message Message to send to backend
   */
  testConnectivity: async (message: string) => {
    try {
      const response = await fetch('/api/connectivity-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Connectivity test failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Connectivity test error:', error);
      throw error;
    }
  }
}
