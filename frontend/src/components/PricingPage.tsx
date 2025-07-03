import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate, Link } from 'react-router-dom';

const PricingPage: React.FC = () => {
  const [currency, setCurrency] = useState('AUD');
  const [exchangeRate, setExchangeRate] = useState(1.0);
  const [freightCost, setFreightCost] = useState(0.0);
  const [freightMode, setFreightMode] = useState('Auto');
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null); // To store a preview of the file content
  const navigate = useNavigate();

  const onDrop = (acceptedFiles: File[]) => {
    const uploadedFile = acceptedFiles[0];
    setFile(uploadedFile);

    // For demonstration, let's just read the file name as a preview
    // In a real application, you'd parse the Excel file and display its content
    setFilePreview(`File uploaded: ${uploadedFile.name} (${(uploadedFile.size / 1024).toFixed(2)} KB)`);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  const handleCalculate = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('currency', currency);
    formData.append('exchange_rate', exchangeRate.toString());
    formData.append('freight_cost', freightCost.toString());
    formData.append('freight_mode', freightMode);

    try {
      const response = await fetch('/api/upload-and-calculate/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': 'Basic ' + btoa('admin:pricing123'), // Replace with actual authentication token
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to calculate prices.');
      }

      const result = await response.json();
      navigate('/results', { state: { processedData: result.processed_data, parameters: result.parameters } });

    } catch (error: any) {
      console.error('Error during calculation:', error);
      alert(`Calculation failed: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200 flex flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
                <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">Configure Pricing & Upload File</h1>

        <div className="absolute top-4 right-4">
          <Link to="/" className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-full text-sm transition-colors duration-200">
            ← Home
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label htmlFor="currency" className="block text-gray-700 text-sm font-bold mb-2">Currency:</label>
            <select
              id="currency"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
            >
              <option value="AUD">AUD</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="JPY">JPY</option>
            </select>
          </div>
          <div>
            <label htmlFor="exchangeRate" className="block text-gray-700 text-sm font-bold mb-2">Exchange Rate:</label>
            <input
              type="number"
              id="exchangeRate"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={exchangeRate}
              onChange={(e) => setExchangeRate(parseFloat(e.target.value))}
              step="0.01"
            />
          </div>
          <div>
            <label htmlFor="freightCost" className="block text-gray-700 text-sm font-bold mb-2">Total Freight Cost (AUD):</label>
            <input
              type="number"
              id="freightCost"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={freightCost}
              onChange={(e) => setFreightCost(parseFloat(e.target.value))}
              step="0.01"
            />
          </div>
          <div>
            <label htmlFor="freightMode" className="block text-gray-700 text-sm font-bold mb-2">Freight Mode:</label>
            <select
              id="freightMode"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={freightMode}
              onChange={(e) => setFreightMode(e.target.value)}
            >
              <option value="Auto">Auto</option>
              <option value="Manual">Manual</option>
            </select>
          </div>
        </div>

        <div
          {...getRootProps()}
          className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-500 transition-colors duration-200 mb-8"
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p className="text-blue-600">Drop the files here ...</p>
          ) : (
            <p className="text-gray-500">Drag 'n' drop your Excel file here, or click to select one</p>
          )}
        </div>

        {filePreview && (
          <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-800">
            {filePreview}
          </div>
        )}

        <div className="text-center">
          <button
            onClick={handleCalculate}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-full text-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-green-300"
          >
            Calculate Prices
          </button>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
