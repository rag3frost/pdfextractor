import { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setFile(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/api/extract', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      // Enhanced data cleaning and normalization
      const cleanedData = {
        ...data.data,
        name: data.data.name ? data.data.name.trim() : null,
        address: data.data.address ? data.data.address.trim() : null,
        phone: data.data.phone ? data.data.phone.trim() : null,
        role: data.data.role ? data.data.role.trim() : null,
      };
      
      console.log('Frontend received data:', data.data); // Debug log
      console.log('Frontend cleaned data:', cleanedData); // Debug log
      
      setResults(cleanedData);
    } catch (err) {
      console.error('Error processing file:', err);
      setError(err.message || 'Error processing file');
    } finally {
      setLoading(false);
    }
  };

  const renderConfidenceBar = (confidence) => {
    const percentage = (confidence * 100).toFixed(0);
    return (
      <div className="confidence-bar">
        <div 
          className="confidence-fill" 
          style={{ 
            width: `${percentage}%`,
            backgroundColor: confidence > 0.7 ? '#4CAF50' : confidence > 0.4 ? '#FFA726' : '#EF5350'
          }}
        />
        <span className="confidence-text">{percentage}%</span>
      </div>
    );
  };

  const renderAddress = (address) => {
    if (!address) return 'Not found';
    
    // Improved address formatting
    const formattedAddress = address
      .split(',')
      .map(part => part.trim())
      .filter(Boolean)
      .join(', ');
    
    return formattedAddress;
  };

  return (
    <div className="container">
      <h1>PDF Information Extractor</h1>
      
      <div className="upload-section">
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="file-input"
        />
        <button 
          onClick={handleSubmit} 
          disabled={!file || loading}
          className="submit-button"
        >
          {loading ? 'Processing...' : 'Extract Information'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {results && (
        <div className="results-section">
          <h2>Extracted Information</h2>
          
          <div className="result-item">
            <h3>Name</h3>
            <p className="result-text">{results.name || 'Not found'}</p>
            {renderConfidenceBar(results.confidence.name)}
          </div>

          <div className="result-item">
            <h3>Phone</h3>
            <p className="result-text">{results.phone || 'Not found'}</p>
            {renderConfidenceBar(results.confidence.phone)}
          </div>

          <div className="result-item">
            <h3>Address</h3>
            <p className="result-text address-text">{renderAddress(results.address)}</p>
            {renderConfidenceBar(results.confidence.address)}
          </div>

          <div className="result-item">
            <h3>Role</h3>
            <p className="result-text">{results.role || 'Not found'}</p>
            {renderConfidenceBar(results.confidence.role)}
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 