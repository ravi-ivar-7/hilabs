import Link from 'next/link';
import { Upload, BarChart3, Shield, Zap, Brain } from 'lucide-react';

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Healthcare Contract Language Classification
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Advanced AI-powered system to classify healthcare contract clauses as Standard or Non-Standard 
          by comparing with state-specific templates. Built for HiLabs Hackathon 2025.
        </p>
        <div className="flex justify-center space-x-4">
          <Link
            href="/upload"  
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Upload className="h-5 w-5" />
            <span>Upload Contract</span>
          </Link>
          <Link
            href="/dashboard"
            className="bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
          >
            <BarChart3 className="h-5 w-5" />
            <span>View Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-3 gap-8 mb-16">
        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Local AI Processing</h3>
          <p className="text-gray-600">
            Uses local AI models for secure, offline contract analysis without external APIs
          </p>
        </div>
        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <Shield className="h-12 w-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Healthcare Compliant</h3>
          <p className="text-gray-600">
            Built with healthcare compliance in mind, including audit trails and validation
          </p>
        </div>
        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <Zap className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Fast & Accurate</h3>
          <p className="text-gray-600">
            Dual-mode processing for both speed and accuracy, optimized for 8GB systems
          </p>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-white rounded-lg shadow-sm p-8">
        <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold mb-2">Upload Contract</h3>
            <p className="text-sm text-gray-600">Upload PDF contracts and select state (TN/WA)</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold mb-2">Extract Clauses</h3>
            <p className="text-sm text-gray-600">AI extracts and identifies key contract clauses</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold mb-2">Compare Templates</h3>
            <p className="text-sm text-gray-600">Compare with state-specific standard templates</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 font-bold">4</span>
            </div>
            <h3 className="font-semibold mb-2">Get Results</h3>
            <p className="text-sm text-gray-600">Receive detailed classification and analysis</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-16 grid md:grid-cols-3 gap-8 text-center">
        <div>
          <div className="text-3xl font-bold text-blue-600">5</div>
          <div className="text-gray-600">Key Attributes Analyzed</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-green-600">2</div>
          <div className="text-gray-600">Supported States (TN, WA)</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-purple-600">100%</div>
          <div className="text-gray-600">Local Processing</div>
        </div>
      </div>
    </div>
  );
}
