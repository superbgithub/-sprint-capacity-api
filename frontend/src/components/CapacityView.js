import React from 'react';

const CapacityView = ({ capacity, onClose }) => {
  if (!capacity) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2>Sprint Capacity: {capacity.sprintId}</h2>
          <button onClick={onClose} style={styles.closeBtn}>×</button>
        </div>

        <div style={styles.content}>
          <div style={styles.summaryGrid}>
            <div style={styles.summaryCard}>
              <h3>Total Working Days</h3>
              <p style={styles.bigNumber}>{capacity.totalWorkingDays}</p>
            </div>

            <div style={styles.summaryCard}>
              <h3>Team Size</h3>
              <p style={styles.bigNumber}>{capacity.teamSize}</p>
            </div>

            <div style={styles.summaryCard}>
              <h3>Total Capacity</h3>
              <p style={styles.bigNumber}>{capacity.totalCapacityDays} days</p>
            </div>

            <div style={styles.summaryCard}>
              <h3>Adjusted Capacity</h3>
              <p style={styles.bigNumber}>{capacity.adjustedTotalCapacity} days</p>
            </div>

            <div style={styles.summaryCard}>
              <h3>Holidays</h3>
              <p style={styles.bigNumber}>{capacity.holidaysCount}</p>
            </div>

            <div style={styles.summaryCard}>
              <h3>Vacation Days</h3>
              <p style={styles.bigNumber}>{capacity.vacationDaysCount}</p>
            </div>
          </div>

          <div style={styles.formula}>
            <strong>Formula:</strong> {capacity.capacityFormula}
          </div>

          <h3>Team Member Breakdown</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Available Days</th>
                <th style={styles.th}>Vacation Days</th>
                <th style={styles.th}>Confidence %</th>
                <th style={styles.th}>Adjusted Capacity</th>
              </tr>
            </thead>
            <tbody>
              {capacity.memberCapacity.map((member) => (
                <tr key={member.memberId}>
                  <td style={styles.td}>{member.memberName}</td>
                  <td style={styles.td}>{member.availableDays}</td>
                  <td style={styles.td}>{member.vacationDays}</td>
                  <td style={styles.td}>{member.confidencePercentage}%</td>
                  <td style={styles.td}><strong>{member.adjustedCapacity}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '8px',
    maxWidth: '900px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    borderBottom: '1px solid #ddd',
  },
  closeBtn: {
    fontSize: '32px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#666',
  },
  content: {
    padding: '20px',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '15px',
    marginBottom: '20px',
  },
  summaryCard: {
    padding: '15px',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    textAlign: 'center',
  },
  bigNumber: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#2196F3',
    margin: '10px 0',
  },
  formula: {
    padding: '15px',
    backgroundColor: '#fff3cd',
    borderRadius: '4px',
    marginBottom: '20px',
    border: '1px solid #ffc107',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '10px',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    backgroundColor: '#2196F3',
    color: 'white',
    borderBottom: '2px solid #ddd',
  },
  td: {
    padding: '12px',
    borderBottom: '1px solid #ddd',
  },
};

export default CapacityView;
