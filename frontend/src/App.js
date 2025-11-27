import React, { useState, useEffect } from 'react';
import SprintForm from './components/SprintForm';
import SprintList from './components/SprintList';
import CapacityView from './components/CapacityView';
import SprintDetail from './components/SprintDetail';
import { sprintService } from './services/api';
import './App.css';

function App() {
  const [sprints, setSprints] = useState([]);
  const [selectedCapacity, setSelectedCapacity] = useState(null);
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [activeView, setActiveView] = useState('list'); // 'list' or 'create'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSprints();
  }, []);

  const loadSprints = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await sprintService.getAllSprints();
      setSprints(data);
    } catch (err) {
      setError('Failed to load sprints: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSprintCreated = async (sprintData) => {
    await sprintService.createSprint(sprintData);
    await loadSprints();
    setActiveView('list');
  };

  const handleViewCapacity = async (sprintId) => {
    try {
      const capacity = await sprintService.getSprintCapacity(sprintId);
      setSelectedCapacity(capacity);
    } catch (err) {
      alert('Failed to load capacity: ' + err.message);
    }
  };

  return (
    <div className="App">
      <header style={styles.header}>
        <h1>Team Capacity Management</h1>
        <nav style={styles.nav}>
          <button
            onClick={() => setActiveView('list')}
            style={activeView === 'list' ? styles.activeTab : styles.tab}
          >
            Sprints
          </button>
          <button
            onClick={() => setActiveView('create')}
            style={activeView === 'create' ? styles.activeTab : styles.tab}
          >
            Create Sprint
          </button>
        </nav>
      </header>

      <main style={styles.main}>
        {error && <div style={styles.error}>{error}</div>}
        {loading && <div style={styles.loading}>Loading...</div>}

        {activeView === 'list' && (
          <SprintList
            sprints={sprints}
            onSprintSelect={setSelectedSprint}
            onViewCapacity={handleViewCapacity}
          />
        )}

        {activeView === 'create' && <SprintForm onSprintCreated={handleSprintCreated} />}
      </main>

      {selectedCapacity && (
        <CapacityView capacity={selectedCapacity} onClose={() => setSelectedCapacity(null)} />
      )}

      {selectedSprint && (
        <SprintDetail sprint={selectedSprint} onClose={() => setSelectedSprint(null)} />
      )}
    </div>
  );
}

const styles = {
  header: {
    backgroundColor: '#2196F3',
    color: 'white',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  nav: {
    marginTop: '15px',
    display: 'flex',
    gap: '10px',
  },
  tab: {
    padding: '10px 20px',
    backgroundColor: 'transparent',
    color: 'white',
    border: '1px solid white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  activeTab: {
    padding: '10px 20px',
    backgroundColor: 'white',
    color: '#2196F3',
    border: '1px solid white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  main: {
    minHeight: 'calc(100vh - 150px)',
  },
  error: {
    padding: '15px',
    backgroundColor: '#f44336',
    color: 'white',
    margin: '20px',
    borderRadius: '4px',
  },
  loading: {
    padding: '20px',
    textAlign: 'center',
    fontSize: '18px',
    color: '#666',
  },
};

export default App;
