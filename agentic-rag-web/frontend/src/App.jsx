import React, { useState, useEffect } from 'react';
import { FileText, Settings, Play, CheckCircle, Activity, Key, FolderOpen } from 'lucide-react';

// API Service
class APIService {
  constructor() {
    this.baseURL = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    this.token = localStorage.getItem('access_token');
  }

  async request(endpoint, options = {}) {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  }

  async login(email, password) {
    const result = await this.request('/api/auth/login', {
      method: 'POST', body: { email, password }
    });
    this.token = result.access_token;
    localStorage.setItem('access_token', this.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    return result;
  }

  async register(email, password, fullName) {
    const result = await this.request('/api/auth/register', {
      method: 'POST', body: { email, password, full_name: fullName }
    });
    this.token = result.access_token;
    localStorage.setItem('access_token', this.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    return result;
  }

  async getStatus() { return this.request('/api/status'); }
  async getDocuments() { return this.request('/api/documents'); }
  async getStats() { return this.request('/api/stats'); }
  async getFolders() { return this.request('/api/setup/folders'); }
  
  async setupCredentials(googleCreds, openaiKey) {
    return this.request('/api/setup/credentials', {
      method: 'POST', body: { google_credentials: googleCreds, openai_api_key: openaiKey }
    });
  }
  
  async selectFolder(folderId, folderName, includeSubfolders = true) {
    return this.request('/api/setup/folder', {
      method: 'POST', body: { folder_id: folderId, folder_name: folderName, include_subfolders: includeSubfolders }
    });
  }
  
  async startScan() { return this.request('/api/scan/manual', { method: 'POST' }); }
}

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) setUser(JSON.parse(storedUser));
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const api = new APIService();
    const result = await api.login(email, password);
    setUser(result.user);
    return result;
  };

  const register = async (email, password, fullName) => {
    const api = new APIService();
    const result = await api.register(email, password, fullName);
    setUser(result.user);
    return result;
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <div className="text-center mb-8">
          <FileText className="w-12 h-12 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">Drive Monitor</h1>
          <p className="text-gray-600">AI-powered document analysis</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <input
              type="text"
              placeholder="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              required
            />
          )}
          
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            required
          />
          
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            required
          />

          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>

          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="w-full text-blue-600 hover:text-blue-700 text-sm"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
};

// Setup Wizard
const SetupWizard = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [googleCreds, setGoogleCreds] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const api = new APIService();

  const handleCredentialsSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      await api.setupCredentials(googleCreds, openaiKey);
      const foldersResult = await api.getFolders();
      setFolders(foldersResult.folders);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderSubmit = async () => {
    setLoading(true);
    try {
      await api.selectFolder(selectedFolder?.id, selectedFolder?.name);
      onComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-8">Setup Your Drive Monitor</h2>

        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Key className="inline w-4 h-4 mr-1" />Google Credentials JSON
              </label>
              <textarea
                value={googleCreds}
                onChange={(e) => setGoogleCreds(e.target.value)}
                placeholder="Paste your Google API credentials JSON here..."
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Get from Google Cloud Console → APIs & Services → Credentials
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">OpenAI API Key</label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {error && <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>}

            <button
              onClick={handleCredentialsSubmit}
              disabled={loading || !googleCreds || !openaiKey}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Validating...' : 'Next: Select Folder'}
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FolderOpen className="inline w-4 h-4 mr-1" />Select Folder to Monitor
              </label>
              <div className="max-h-64 overflow-y-auto border border-gray-300 rounded-md">
                {folders.map((folder) => (
                  <div
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder)}
                    className={`p-3 cursor-pointer hover:bg-gray-50 ${
                      selectedFolder?.id === folder.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                    }`}
                  >
                    {folder.name}
                  </div>
                ))}
              </div>
            </div>

            {error && <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>}

            <div className="flex space-x-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400"
              >
                Back
              </button>
              <button
                onClick={handleFolderSubmit}
                disabled={loading || !selectedFolder}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Setting up...' : 'Complete Setup'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Dashboard Components
const StatusCard = ({ title, value, icon: Icon, color = "blue" }) => {
  const colors = { blue: "bg-blue-500", green: "bg-green-500", yellow: "bg-yellow-500", red: "bg-red-500" };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colors[color]} text-white`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

const DocumentCard = ({ document }) => {
  const priorityColors = {
    high: "border-red-500 bg-red-50",
    medium: "border-yellow-500 bg-yellow-50", 
    low: "border-green-500 bg-green-50"
  };

  return (
    <div className={`p-4 rounded-lg border-l-4 ${priorityColors[document.priority]} mb-4`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-900">{document.name}</h3>
        <span className="text-xs font-medium text-gray-500">{document.priority.toUpperCase()}</span>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{document.summary}</p>
      
      {document.action_items.length > 0 && (
        <div className="mb-2">
          <h4 className="text-sm font-medium text-gray-700 mb-1">Action Items:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            {document.action_items.slice(0, 3).map((item, index) => (
              <li key={index} className="flex items-start">
                <CheckCircle className="w-3 h-3 mr-2 mt-0.5 text-green-500" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="text-xs text-gray-500">
        Processed {new Date(document.processed_at).toLocaleDateString()}
      </div>
    </div>
  );
};

// Main Dashboard
const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const api = new APIService();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statusData, documentsData, statsData] = await Promise.all([
        api.getStatus(), api.getDocuments(), api.getStats()
      ]);
      setStatus(statusData);
      setDocuments(documentsData.documents || []);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      await api.startScan();
      setTimeout(loadData, 3000);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Drive Monitor</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleScan}
                disabled={scanning}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Play className="w-4 h-4 mr-2" />
                {scanning ? 'Scanning...' : 'Run Scan'}
              </button>
              
              <button 
                onClick={() => { localStorage.clear(); window.location.reload(); }}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatusCard title="Total Documents" value={stats?.documents_processed || 0} icon={FileText} />
            <StatusCard title="Action Items" value={stats?.actions_created || 0} icon={CheckCircle} color="green" />
            <StatusCard title="Scans Performed" value={stats?.scans_performed || 0} icon={Activity} color="yellow" />
            <StatusCard 
              title="Folder Status" 
              value={status?.folder_name ? "Active" : "Not Set"} 
              icon={FolderOpen} 
              color={status?.folder_name ? "green" : "red"} 
            />
          </div>

          {/* Status Summary */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Monitoring Folder</p>
                <p className="font-medium">{status?.folder_name || 'Not configured'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Documents</p>
                <p className="font-medium">{status?.total_documents || 0}</p>
              </div>
            </div>
          </div>

          {/* Recent Documents */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Documents</h2>
            {documents.length > 0 ? (
              <div className="space-y-4">
                {documents.map((doc) => (
                  <DocumentCard key={doc.file_id} document={doc} />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No documents processed yet. Click "Run Scan" to get started! 🚀
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

// Main App
const App = () => {
  const { user, loading } = React.useContext(AuthContext);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);

  useEffect(() => {
    if (user) {
      const api = new APIService();
      api.getStatus()
        .then(status => setNeedsSetup(status.status === 'setup_needed'))
        .catch(() => setNeedsSetup(true))
        .finally(() => setCheckingSetup(false));
    } else {
      setCheckingSetup(false);
    }
  }, [user]);

  if (loading || checkingSetup) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Activity className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!user) return <LoginForm />;
  if (needsSetup) return <SetupWizard onComplete={() => setNeedsSetup(false)} />;
  return <Dashboard />;
};

// Root Component
export default function DriveMonitorApp() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}