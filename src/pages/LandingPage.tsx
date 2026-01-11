// Landing page - professional entry point for audit trail system

import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      {/* Centered content container */}
      <div className="max-w-3xl w-full text-center">
        {/* Main heading */}
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
          Audit Trail System
        </h1>
        
        {/* Subheading with emphasis */}
        <h2 className="text-3xl md:text-4xl font-bold text-blue-600 mb-8">
          Every Action, Tracked
        </h2>

        {/* Value proposition - clear and concise */}
        <p className="text-lg text-gray-600 leading-relaxed mb-12 max-w-2xl mx-auto">
          Production-grade audit logging for modern applications. Track user actions, 
          ensure compliance, and investigate incidents with complete transparency. 
          Built with security and scalability in mind.
        </p>

        {/* Call-to-action buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {/* Primary action - create account */}
          <Link
            to="/register"
            className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            Create Account
          </Link>

          {/* Secondary action - sign in */}
          <Link
            to="/login"
            className="px-8 py-3 bg-white text-blue-600 font-semibold rounded-lg border-2 border-blue-600 hover:bg-blue-50 transition-colors"
          >
            Login In
          </Link>
        </div>

      
      </div>
    </div>
  );
}