import React from 'react';
import { useLocation, Link } from 'react-router-dom';

interface ResultsPageProps {
  // Define props if data is passed directly, otherwise fetch from context/backend
}

const ResultsPage: React.FC<ResultsPageProps> = () => {
  const location = useLocation();
  const { processedData, parameters } = location.state || {};

  const handleDownloadCsv = async () => {
    try {
      const response = await fetch('/api/export-csv/', {
        headers: {
          'Authorization': 'Basic ' + btoa('admin:pricing123'), // Replace with actual authentication token
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'priced_parts.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading CSV:', error);
      alert('Failed to download CSV. Please try again.');
    }
  };

  if (!processedData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200 flex items-center justify-center p-8">
        <div className="max-w-4xl w-full bg-white p-10 rounded-2xl shadow-xl border border-gray-100 text-center">
          <h2 className="text-2xl font-bold text-gray-800">No results to display. Please go back and upload a file.</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200 flex flex-col items-center p-8">
      <div className="max-w-6xl w-full bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
                <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">Calculation Results</h1>

        <div className="absolute top-4 right-4">
          <Link to="/" className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-full text-sm transition-colors duration-200">
            ← Home
          </Link>
        </div>

        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Input Parameters:</h2>
          <div className="grid grid-cols-2 gap-4 text-gray-600">
            <p><strong>Currency:</strong> {parameters?.currency}</p>
            <p><strong>Exchange Rate:</strong> {parameters?.exchange_rate}</p>
            <p><strong>Freight Cost:</strong> {parameters?.freight_cost}</p>
            <p><strong>Freight Mode:</strong> {parameters?.freight_mode}</p>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-gray-700 mb-4">Processed Data:</h2>
        <div className="overflow-x-auto mb-8">
          <table className="min-w-full bg-white border border-gray-300 rounded-lg shadow-sm">
            <thead className="bg-gray-100">
              <tr>
                {Object.keys(processedData[0]).map((key) => (
                  <th key={key} className="py-3 px-4 border-b text-left text-sm font-semibold text-gray-700 uppercase tracking-wider">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {processedData.map((row: any, index: number) => (
                <tr key={index} className="hover:bg-gray-50">
                  {Object.values(row).map((value: any, idx: number) => (
                    <td key={idx} className="py-2 px-4 border-b text-sm text-gray-800">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={handleDownloadCsv}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-full text-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-300"
          >
            Download Results as CSV
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
