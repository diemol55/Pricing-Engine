import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGetStartedClick = () => {
    navigate('/pricing');
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200 flex flex-col items-center justify-center p-8">
      <div className="max-w-5xl w-full bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
        <h1 className="text-5xl font-extrabold text-center text-gray-900 mb-12 leading-tight">
          <span className="block">📦 Ozwide Pricing Calculator</span>
          <span className="block text-2xl font-medium text-blue-600 mt-2">Streamline Your Pricing Process</span>
        </h1>

        <div className="grid grid-cols-1 gap-10">
          <div className="space-y-8">
            <StepItem
              step="1"
              title="Upload Your File"
              description="Start by uploading your purchase file in Excel format (.xlsx or .xls). The application will read the data and prepare it for the pricing calculation."
            />
            <StepItem
              step="2"
              title="Configure Pricing"
              description="Set the currency, exchange rate, and freight costs. You can also choose between automatic and manual freight cost allocation."
            />
          </div>
          <div className="space-y-8">
            
            <StepItem
              step="3"
              title="Calculate and View Results"
              description='Once you are ready, click the "Calculate" button to process the data and view the final pricing tiers. You can then export the results to a CSV file.'
            />
          </div>
        </div>

        <div className="text-center mt-16">
          <button onClick={handleGetStartedClick} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-12 rounded-full text-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-300">
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
};

interface StepItemProps {
  step: string;
  title: string;
  description: string;
}

const StepItem: React.FC<StepItemProps> = ({ step, title, description }) => {
  return (
    <div className="flex items-start space-x-5">
      <div className="flex-shrink-0 w-14 h-14 bg-blue-500 text-white rounded-full flex items-center justify-center text-3xl font-extrabold shadow-md">
        {step}
      </div>
      <div>
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">{title}</h2>
        <p className="text-gray-600 leading-relaxed">{description}</p>
      </div>
    </div>
  );
};

export default LandingPage;