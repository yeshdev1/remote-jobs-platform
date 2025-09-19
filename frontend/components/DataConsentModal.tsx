'use client';

import { useState, useEffect } from 'react';

interface DataConsentModalProps {
  onConsent: (accepted: boolean) => void;
}

export default function DataConsentModal({ onConsent }: DataConsentModalProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [hasAccepted, setHasAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if user has already given consent
    const consentGiven = localStorage.getItem('dataConsentGiven');
    const consentTimestamp = localStorage.getItem('dataConsentTimestamp');
    
    if (consentGiven === 'true' && consentTimestamp) {
      // Check if consent is still valid (6 months)
      const sixMonthsAgo = Date.now() - (6 * 30 * 24 * 60 * 60 * 1000);
      if (parseInt(consentTimestamp) > sixMonthsAgo) {
        onConsent(true);
        return;
      }
    }
    
    // Show modal if no valid consent
    setIsVisible(true);
  }, [onConsent]);

  const handleAccept = () => {
    if (!hasAccepted) return;
    
    setIsLoading(true);
    
    // Store consent in localStorage
    localStorage.setItem('dataConsentGiven', 'true');
    localStorage.setItem('dataConsentTimestamp', Date.now().toString());
    localStorage.setItem('dataConsentDetails', JSON.stringify({
      analyticsConsent: true,
      marketingConsent: true,
      timestamp: new Date().toISOString(),
      version: '1.0'
    }));
    
    setTimeout(() => {
      setIsVisible(false);
      onConsent(true);
      setIsLoading(false);
    }, 500);
  };

  const handleDecline = () => {
    setIsLoading(true);
    
    // Store minimal consent (essential cookies only)
    localStorage.setItem('dataConsentGiven', 'false');
    localStorage.setItem('dataConsentTimestamp', Date.now().toString());
    localStorage.setItem('dataConsentDetails', JSON.stringify({
      analyticsConsent: false,
      marketingConsent: false,
      timestamp: new Date().toISOString(),
      version: '1.0'
    }));
    
    setTimeout(() => {
      setIsVisible(false);
      onConsent(false);
      setIsLoading(false);
    }, 500);
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="p-6 border-b border-gray-200/50">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Privacy & Data Consent</h2>
            </div>
            <p className="text-gray-600">We value your privacy and want to be transparent about how we use your data.</p>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Data Collection Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Data Collection & Analytics
              </h3>
              <p className="text-blue-800 text-sm leading-relaxed">
                We collect analytics data to improve your experience on Remote Away. This includes page views, 
                search queries, job interactions, and usage patterns. This data helps us understand how users 
                navigate our platform and find relevant job opportunities.
              </p>
            </div>

            {/* Data Usage */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">How We Use Your Data:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Platform Analytics</p>
                    <p className="text-sm text-gray-600">Track usage patterns and improve user experience</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Job Market Insights</p>
                    <p className="text-sm text-gray-600">Analyze job trends and salary data</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Performance Optimization</p>
                    <p className="text-sm text-gray-600">Monitor site performance and loading times</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Content Personalization</p>
                    <p className="text-sm text-gray-600">Customize job recommendations based on preferences</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Data Sharing Notice */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <h3 className="font-semibold text-amber-900 mb-2 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Data Sharing & Monetization
              </h3>
              <p className="text-amber-800 text-sm leading-relaxed">
                <strong>Important:</strong> Aggregated and anonymized analytics data may be shared with partners 
                or sold to third parties for market research purposes. This helps fund our platform and keep 
                our job board services free. No personally identifiable information is shared.
              </p>
            </div>

            {/* Legal Compliance */}
            <div className="text-sm text-gray-600 space-y-2">
              <p><strong>Legal Basis:</strong> Your consent (GDPR Article 6(1)(a), CCPA compliance)</p>
              <p><strong>Data Retention:</strong> Analytics data is retained for 24 months</p>
              <p><strong>Your Rights:</strong> You can withdraw consent, request data deletion, or access your data at any time</p>
              <p><strong>Contact:</strong> For privacy questions, email privacy@remote-away.com</p>
            </div>

            {/* Consent Checkbox */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasAccepted}
                  onChange={(e) => setHasAccepted(e.target.checked)}
                  className="mt-1 w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                />
                <div>
                  <p className="font-medium text-gray-900">I consent to data collection and analytics</p>
                  <p className="text-sm text-gray-600 mt-1">
                    I understand that my usage data will be collected for analytics purposes and may be 
                    shared in anonymized form with third parties. I can withdraw this consent at any time.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200/50 flex flex-col sm:flex-row gap-3 sm:justify-end">
            <button
              onClick={handleDecline}
              disabled={isLoading}
              className="px-6 py-3 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : 'Decline & Continue'}
            </button>
            
            <button
              onClick={handleAccept}
              disabled={!hasAccepted || isLoading}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Processing...</span>
                </div>
              ) : (
                'Accept & Continue'
              )}
            </button>
          </div>

          {/* Privacy Policy Link */}
          <div className="px-6 pb-6 text-center">
            <p className="text-xs text-gray-500">
              By using this site, you also agree to our{' '}
              <a href="/privacy-policy" className="text-blue-600 hover:underline">Privacy Policy</a>
              {' '}and{' '}
              <a href="/terms-of-service" className="text-blue-600 hover:underline">Terms of Service</a>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
