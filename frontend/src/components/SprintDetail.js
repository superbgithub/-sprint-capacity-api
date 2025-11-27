import React from 'react';

const SprintDetail = ({ sprint, onClose }) => {
  if (!sprint) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2>{sprint.sprintName || `Sprint ${sprint.sprintNumber}`}</h2>
          <button onClick={onClose} style={styles.closeBtn}>×</button>
        </div>

        <div style={styles.content}>
          <div style={styles.section}>
            <h3>Sprint Information</h3>
            <div style={styles.infoGrid}>
              <div style={styles.infoItem}>
                <strong>Sprint Number:</strong> {sprint.sprintNumber}
              </div>
              <div style={styles.infoItem}>
                <strong>Duration:</strong> {sprint.sprintDuration} days
              </div>
              <div style={styles.infoItem}>
                <strong>Start Date:</strong> {sprint.startDate}
              </div>
              <div style={styles.infoItem}>
                <strong>End Date:</strong> {sprint.endDate}
              </div>
              <div style={styles.infoItem}>
                <strong>Confidence:</strong> {sprint.confidencePercentage}%
              </div>
              <div style={styles.infoItem}>
                <strong>Created:</strong> {new Date(sprint.createdAt).toLocaleString()}
              </div>
            </div>
          </div>

          {sprint.holidays && sprint.holidays.length > 0 && (
            <div style={styles.section}>
              <h3>Sprint Holidays ({sprint.holidays.length})</h3>
              <div style={styles.holidayList}>
                {sprint.holidays.map((holiday) => (
                  <div key={holiday.id} style={styles.holidayCard}>
                    <div><strong>{holiday.holidayDate}</strong></div>
                    <div>{holiday.name}</div>
                    {holiday.description && (
                      <div style={styles.description}>{holiday.description}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={styles.section}>
            <h3>Team Members ({sprint.teamMembers.length})</h3>
            {sprint.teamMembers.map((member) => (
              <div key={member.id} style={styles.memberCard}>
                <div style={styles.memberHeader}>
                  <h4>{member.name}</h4>
                  <span style={styles.roleBadge}>{member.role}</span>
                </div>
                <div style={styles.memberInfo}>
                  {member.vacations && member.vacations.length > 0 && (
                    <div style={styles.vacations}>
                      <strong>Vacations:</strong>
                      <ul style={styles.vacationList}>
                        {member.vacations.map((vacation) => (
                          <li key={vacation.id}>
                            {vacation.startDate} to {vacation.endDate}
                            {vacation.reason && ` (${vacation.reason})`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
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
    maxWidth: '800px',
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
    backgroundColor: '#2196F3',
    color: 'white',
    borderRadius: '8px 8px 0 0',
  },
  closeBtn: {
    fontSize: '32px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: 'white',
  },
  content: {
    padding: '20px',
  },
  section: {
    marginBottom: '30px',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '15px',
    marginTop: '10px',
  },
  infoItem: {
    padding: '10px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
  },
  memberCard: {
    padding: '15px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginBottom: '10px',
    backgroundColor: '#fafafa',
  },
  memberHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  roleBadge: {
    padding: '4px 12px',
    backgroundColor: '#4CAF50',
    color: 'white',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  memberInfo: {
    fontSize: '14px',
  },
  vacations: {
    marginTop: '10px',
  },
  vacationList: {
    marginTop: '5px',
    marginLeft: '20px',
    fontSize: '13px',
  },
  holidayList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '15px',
    marginTop: '10px',
  },
  holidayCard: {
    padding: '15px',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: '4px',
    display: 'flex',
    flexDirection: 'column',
    gap: '5px',
  },
  description: {
    fontSize: '12px',
    color: '#666',
  },
};

export default SprintDetail;
