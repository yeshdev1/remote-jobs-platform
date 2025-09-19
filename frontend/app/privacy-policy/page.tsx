'use client';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-300 bg-clip-text text-transparent mb-4">
              Privacy Policy
            </h1>
            <p className="text-gray-300">
              Last updated: {new Date().toLocaleDateString()}
            </p>
          </div>

          <div className="space-y-8 text-gray-200">
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">1. Information We Collect</h2>
              <div className="space-y-4">
                <p>
                  We collect information you provide directly to us, such as when you create an account, 
                  use our services, or communicate with us. This may include:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Usage data and analytics (page views, search queries, job interactions)</li>
                  <li>Device information (browser type, IP address, operating system)</li>
                  <li>Cookies and similar tracking technologies</li>
                  <li>Job preferences and search history</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">2. How We Use Your Information</h2>
              <div className="space-y-4">
                <p>We use the information we collect to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Provide, maintain, and improve our services</li>
                  <li>Analyze usage patterns and optimize user experience</li>
                  <li>Generate aggregated market insights and job trends</li>
                  <li>Customize job recommendations and content</li>
                  <li>Monitor platform performance and security</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">3. Data Sharing and Sales</h2>
              <div className="bg-amber-50/10 border border-amber-200/30 rounded-lg p-4 mb-4">
                <p className="text-amber-200 font-medium">
                  <strong>Important:</strong> We may share or sell aggregated, anonymized data to third parties.
                </p>
              </div>
              <div className="space-y-4">
                <p>
                  We may share aggregated and anonymized analytics data with:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Market research companies for job market analysis</li>
                  <li>HR technology partners for industry insights</li>
                  <li>Academic institutions for employment studies</li>
                  <li>Business partners for platform optimization</li>
                </ul>
                <p>
                  <strong>No personally identifiable information is included in shared data.</strong> 
                  All data is aggregated and anonymized before sharing or sale.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">4. Your Rights and Choices</h2>
              <div className="space-y-4">
                <p>You have the right to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Withdraw consent for data collection at any time</li>
                  <li>Request access to your personal data</li>
                  <li>Request deletion of your data</li>
                  <li>Opt out of data sharing and sales</li>
                  <li>Correct inaccurate personal information</li>
                </ul>
                <p>
                  To exercise these rights, contact us at{' '}
                  <a href="mailto:privacy@remote-away.com" className="text-blue-400 hover:underline">
                    privacy@remote-away.com
                  </a>
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">5. Data Security</h2>
              <p>
                We implement appropriate technical and organizational measures to protect your personal 
                information against unauthorized access, alteration, disclosure, or destruction. However, 
                no method of transmission over the internet is 100% secure.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">6. Data Retention</h2>
              <p>
                We retain analytics data for 24 months from collection. After this period, data is 
                automatically deleted unless required for legal compliance or legitimate business purposes.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">7. International Data Transfers</h2>
              <p>
                Your information may be transferred to and processed in countries other than your country 
                of residence. We ensure appropriate safeguards are in place for such transfers.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">8. Children's Privacy</h2>
              <p>
                Our services are not intended for children under 16. We do not knowingly collect 
                personal information from children under 16.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">9. Changes to This Policy</h2>
              <p>
                We may update this privacy policy from time to time. We will notify you of any 
                material changes by posting the new policy on this page and updating the "Last updated" date.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">10. Contact Us</h2>
              <div className="space-y-2">
                <p>If you have questions about this privacy policy, please contact us:</p>
                <div className="bg-white/5 rounded-lg p-4">
                  <p><strong>Email:</strong> privacy@remote-away.com</p>
                  <p><strong>Address:</strong> Remote Away Privacy Team</p>
                  <p><strong>Response Time:</strong> We respond to privacy requests within 30 days</p>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-white/20">
            <div className="flex justify-between items-center">
              <a 
                href="/"
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                ← Back to Jobs
              </a>
              
              <div className="text-sm text-gray-400">
                <p>This policy complies with GDPR and CCPA requirements</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
