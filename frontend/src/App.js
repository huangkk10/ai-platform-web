import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('Loading...');
  const [apiData, setApiData] = useState(null);

  useEffect(() => {
    // 測試 Django API 連線
    const testAPI = async () => {
      try {
        const response = await axios.get('/api/');
        setApiStatus('Connected');
        setApiData(response.data);
      } catch (error) {
        console.log('API Error:', error);
        if (error.response?.status === 403) {
          setApiStatus('API Available (Authentication Required)');
          setApiData({ message: 'API is running but requires authentication' });
        } else if (error.response?.status === 401) {
          setApiStatus('API Available (Unauthorized)');
          setApiData({ message: 'API is running but user needs to login' });
        } else if (error.response?.status === 400) {
          setApiStatus('API Available (Bad Request)');
          setApiData({ message: 'API is running but request format needs adjustment' });
        } else {
          setApiStatus('Connection Failed');
          setApiData({ 
            error: `Request failed with status code ${error.response?.status || 'unknown'}`,
            message: error.message 
          });
        }
      }
    };

    testAPI();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 AI Platform</h1>
        <p>Welcome to the AI Platform Web Application</p>
        
        <div className="status-section">
          <h2>System Status</h2>
          <div className="status-item">
            <span className="status-label">Django API:</span>
            <span className={`status-value ${apiStatus === 'Connected' || apiStatus.includes('Available') ? 'success' : 'error'}`}>
              {apiStatus}
            </span>
          </div>
          
          {apiData && (
            <div className="api-data">
              <h3>API Response:</h3>
              <pre>{JSON.stringify(apiData, null, 2)}</pre>
            </div>
          )}
        </div>

        <div className="services-section">
          <h2>Available Services</h2>
          <div className="service-links">
            <a href="/admin/" target="_blank" rel="noopener noreferrer">
              Django Admin
            </a>
            <a href="/api/" target="_blank" rel="noopener noreferrer">
              API Endpoints
            </a>
            <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer">
              Database Admin (Adminer)
            </a>
            <a href="http://localhost:9000" target="_blank" rel="noopener noreferrer">
              Container Manager (Portainer)
            </a>
          </div>
        </div>

        <div className="info-section">
          <h2>Development Info</h2>
          <ul>
            <li>React Frontend: Port 3000</li>
            <li>Django Backend: Port 8000</li>
            <li>PostgreSQL Database: Port 5432</li>
            <li>Nginx Reverse Proxy: Port 80/443</li>
          </ul>
        </div>
      </header>
    </div>
  );
}

export default App;