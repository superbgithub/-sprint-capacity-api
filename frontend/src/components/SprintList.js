import React from 'react';

const SprintList = ({ sprints, onSprintSelect, onViewCapacity }) => {
  return (
    <div style={styles.container}>
      <h2>Sprints</h2>
      {sprints.length === 0 ? (
        <p>No sprints found. Create one to get started!</p>
      ) : (
        <div style={styles.grid}>
          {sprints.map((sprint) => (
            <div key={sprint.id} style={styles.card}>
              <h3>{sprint.sprintName || `Sprint ${sprint.sprintNumber}`}</h3>
              <div style={styles.info}>
                <p><strong>Sprint #:</strong> {sprint.sprintNumber}</p>
                <p><strong>Duration:</strong> {sprint.sprintDuration} days</p>
                <p><strong>Start:</strong> {sprint.startDate}</p>
                <p><strong>End:</strong> {sprint.endDate}</p>
                <p><strong>Team Size:</strong> {sprint.teamMembers.length}</p>
                <p><strong>Holidays:</strong> {sprint.holidays?.length || 0}</p>
              </div>
              <div style={styles.buttonGroup}>
                <button onClick={() => onSprintSelect(sprint)} style={styles.viewBtn}>
                  View Details
                </button>
                <button onClick={() => onViewCapacity(sprint.id)} style={styles.capacityBtn}>
                  View Capacity
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '20px',
  },
  card: {
    padding: '20px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: '#fff',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  info: {
    marginTop: '10px',
    fontSize: '14px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '10px',
    marginTop: '15px',
  },
  viewBtn: {
    padding: '8px 16px',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1,
  },
  capacityBtn: {
    padding: '8px 16px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1,
  },
};

export default SprintList;
