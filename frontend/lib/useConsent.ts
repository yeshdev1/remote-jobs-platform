import { useState, useEffect } from 'react';

interface ConsentDetails {
  analyticsConsent: boolean;
  marketingConsent: boolean;
  timestamp: string;
  version: string;
}

interface ConsentState {
  hasConsent: boolean | null; // null = not determined yet, true/false = user decision
  consentDetails: ConsentDetails | null;
  isLoading: boolean;
}

export const useConsent = () => {
  const [consentState, setConsentState] = useState<ConsentState>({
    hasConsent: null,
    consentDetails: null,
    isLoading: true
  });

  useEffect(() => {
    checkExistingConsent();
  }, []); 

  const checkExistingConsent = () => {
    try {
      const consentGiven = localStorage.getItem('dataConsentGiven');
      const consentTimestamp = localStorage.getItem('dataConsentTimestamp');
      const consentDetailsStr = localStorage.getItem('dataConsentDetails');

      if (consentGiven && consentTimestamp && consentDetailsStr) {
        // Check if consent is still valid (6 months)
        const sixMonthsAgo = Date.now() - (6 * 30 * 24 * 60 * 60 * 1000);
        const timestamp = parseInt(consentTimestamp);
        
        if (timestamp > sixMonthsAgo) {
          const consentDetails = JSON.parse(consentDetailsStr);
          setConsentState({
            hasConsent: consentGiven === 'true',
            consentDetails,
            isLoading: false
          });
          return;
        } else {
          // Consent expired, clear old data
          clearConsent();
        }
      }

      // No valid consent found
      setConsentState({
        hasConsent: null,
        consentDetails: null,
        isLoading: false
      });
    } catch (error) {
      console.error('Error checking consent:', error);
      setConsentState({
        hasConsent: null,
        consentDetails: null,
        isLoading: false
      });
    }
  };

  const giveConsent = (accepted: boolean) => {
    const consentDetails: ConsentDetails = {
      analyticsConsent: accepted,
      marketingConsent: accepted,
      timestamp: new Date().toISOString(),
      version: '1.0'
    };

    try {
      localStorage.setItem('dataConsentGiven', accepted.toString());
      localStorage.setItem('dataConsentTimestamp', Date.now().toString());
      localStorage.setItem('dataConsentDetails', JSON.stringify(consentDetails));

      setConsentState({
        hasConsent: accepted,
        consentDetails,
        isLoading: false
      });

      // Track consent decision (only if analytics consent is given)
      if (accepted && typeof window !== 'undefined') {
        // Initialize analytics tracking here
        console.log('Analytics consent given - initializing tracking');
        // You can add Google Analytics, Mixpanel, or other analytics here
      }
    } catch (error) {
      console.error('Error saving consent:', error);
    }
  };

  const withdrawConsent = () => {
    clearConsent();
    setConsentState({
      hasConsent: false,
      consentDetails: {
        analyticsConsent: false,
        marketingConsent: false,
        timestamp: new Date().toISOString(),
        version: '1.0'
      },
      isLoading: false
    });
  };

  const clearConsent = () => {
    try {
      localStorage.removeItem('dataConsentGiven');
      localStorage.removeItem('dataConsentTimestamp');
      localStorage.removeItem('dataConsentDetails');
    } catch (error) {
      console.error('Error clearing consent:', error);
    }
  };

  const updateConsent = (updates: Partial<ConsentDetails>) => {
    if (!consentState.consentDetails) return;

    const updatedDetails = {
      ...consentState.consentDetails,
      ...updates,
      timestamp: new Date().toISOString()
    };

    try {
      localStorage.setItem('dataConsentDetails', JSON.stringify(updatedDetails));
      setConsentState(prev => ({
        ...prev,
        consentDetails: updatedDetails
      }));
    } catch (error) {
      console.error('Error updating consent:', error);
    }
  };

  // Helper functions for analytics tracking
  const canTrackAnalytics = () => {
    return consentState.hasConsent === true && 
           consentState.consentDetails?.analyticsConsent === true;
  };

  const canUseMarketing = () => {
    return consentState.hasConsent === true && 
           consentState.consentDetails?.marketingConsent === true;
  };

  const trackEvent = (eventName: string, properties?: Record<string, any>) => {
    if (!canTrackAnalytics()) {
      console.log('Analytics tracking blocked - no consent');
      return;
    }

    // Track the event (implement your analytics provider here)
    console.log('Tracking event:', eventName, properties);
    
    // Example implementations:
    // Google Analytics
    // gtag('event', eventName, properties);
    
    // Mixpanel
    // mixpanel.track(eventName, properties);
    
    // Custom analytics
    // customAnalytics.track(eventName, properties);
  };

  const trackPageView = (path: string, title?: string) => {
    if (!canTrackAnalytics()) {
      console.log('Page view tracking blocked - no consent');
      return;
    }

    console.log('Tracking page view:', path, title);
    
    // Implement your page view tracking here
    // gtag('config', 'GA_MEASUREMENT_ID', { page_path: path, page_title: title });
  };

  return {
    ...consentState,
    giveConsent,
    withdrawConsent,
    updateConsent,
    canTrackAnalytics,
    canUseMarketing,
    trackEvent,
    trackPageView,
    needsConsent: consentState.hasConsent === null && !consentState.isLoading
  };
};
