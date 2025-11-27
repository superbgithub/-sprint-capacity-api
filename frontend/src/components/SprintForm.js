import React, { useState } from 'react';

const SprintForm = ({ onSprintCreated }) => {
  const [formData, setFormData] = useState({
    sprintNumber: '',
    startDate: '',
    endDate: '',
    confidencePercentage: 100,
    teamMembers: [{ name: '', role: 'Developer', vacations: [] }],
    holidays: [],
  });

  const [newHoliday, setNewHoliday] = useState({ holidayDate: '', name: '', description: '' });
  const [newVacation, setNewVacation] = useState({ memberIndex: 0, startDate: '', endDate: '', reason: '' });

  const roles = ['Developer', 'Tester', 'Designer', 'Product Owner', 'Scrum Master', 'Tech Lead'];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleTeamMemberChange = (index, field, value) => {
    const updatedMembers = [...formData.teamMembers];
    updatedMembers[index][field] = value;
    setFormData({ ...formData, teamMembers: updatedMembers });
  };

  const addTeamMember = () => {
    setFormData({
      ...formData,
      teamMembers: [...formData.teamMembers, { name: '', role: 'Developer', vacations: [] }],
    });
  };

  const removeTeamMember = (index) => {
    const updatedMembers = formData.teamMembers.filter((_, i) => i !== index);
    setFormData({ ...formData, teamMembers: updatedMembers });
  };

  const addHoliday = () => {
    if (newHoliday.holidayDate && newHoliday.name) {
      setFormData({
        ...formData,
        holidays: [...formData.holidays, newHoliday],
      });
      setNewHoliday({ holidayDate: '', name: '', description: '' });
    }
  };

  const removeHoliday = (index) => {
    const updatedHolidays = formData.holidays.filter((_, i) => i !== index);
    setFormData({ ...formData, holidays: updatedHolidays });
  };



  const addVacation = () => {
    if (newVacation.startDate && newVacation.endDate) {
      const updatedMembers = [...formData.teamMembers];
      updatedMembers[newVacation.memberIndex].vacations.push({
        startDate: newVacation.startDate,
        endDate: newVacation.endDate,
        reason: newVacation.reason,
      });
      setFormData({ ...formData, teamMembers: updatedMembers });
      setNewVacation({ memberIndex: 0, startDate: '', endDate: '', reason: '' });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onSprintCreated(formData);
      // Reset form
      setFormData({
        sprintNumber: '',
        startDate: '',
        endDate: '',
        confidencePercentage: 100,
        teamMembers: [{ name: '', role: 'Developer', vacations: [] }],
        holidays: [],
      });
      alert('Sprint created successfully!');
    } catch (error) {
      alert('Error creating sprint: ' + (error.response?.data?.message || error.message));
    }
  };

  return (
    <div style={styles.container}>
      <h2>Create New Sprint</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.formGroup}>
          <label>Sprint Number (YY-NN):</label>
          <input
            type="text"
            name="sprintNumber"
            value={formData.sprintNumber}
            onChange={handleChange}
            placeholder="e.g., 25-01"
            required
            style={styles.input}
            maxLength="5"
          />
          <small style={{ fontSize: '12px', color: '#666', marginTop: '4px', display: 'block' }}>
            Format: YY-NN (e.g., 25-01 for Sprint 1 of 2025)
          </small>
        </div>

        <div style={styles.formRow}>
          <div style={styles.formGroup}>
            <label>Start Date:</label>
            <input
              type="date"
              name="startDate"
              value={formData.startDate}
              onChange={handleChange}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>End Date:</label>
            <input
              type="date"
              name="endDate"
              value={formData.endDate}
              onChange={handleChange}
              required
              style={styles.input}
            />
          </div>
        </div>

        <div style={styles.formGroup}>
          <label>Sprint Confidence %:</label>
          <input
            type="number"
            name="confidencePercentage"
            value={formData.confidencePercentage}
            onChange={handleChange}
            min="0"
            max="100"
            step="0.1"
            style={styles.input}
          />
          <small style={{ fontSize: '12px', color: '#666', marginTop: '4px', display: 'block' }}>
            Overall confidence for sprint capacity forecasting (0-100%)
          </small>
        </div>

        <h3>Team Members</h3>
        {formData.teamMembers.map((member, index) => (
          <div key={index} style={styles.memberCard}>
            <div style={styles.formRow}>
              <div style={styles.formGroup}>
                <label>Name:</label>
                <input
                  type="text"
                  value={member.name}
                  onChange={(e) => handleTeamMemberChange(index, 'name', e.target.value)}
                  required
                  style={styles.input}
                />
              </div>

              <div style={styles.formGroup}>
                <label>Role:</label>
                <select
                  value={member.role}
                  onChange={(e) => handleTeamMemberChange(index, 'role', e.target.value)}
                  style={styles.input}
                >
                  {roles.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>

              <button type="button" onClick={() => removeTeamMember(index)} style={styles.removeBtn}>
                Remove
              </button>
            </div>

            {member.vacations.length > 0 && (
              <div style={styles.vacationsList}>
                <strong>Vacations:</strong>
                {member.vacations.map((vac, vIdx) => (
                  <div key={vIdx} style={styles.vacationItem}>
                    {vac.startDate} to {vac.endDate} {vac.reason && `(${vac.reason})`}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        <button type="button" onClick={addTeamMember} style={styles.addBtn}>
          + Add Team Member
        </button>

        <h3>Add Vacation</h3>
        <div style={styles.formRow}>
          <div style={styles.formGroup}>
            <label>Team Member:</label>
            <select
              value={newVacation.memberIndex}
              onChange={(e) => setNewVacation({ ...newVacation, memberIndex: parseInt(e.target.value) })}
              style={styles.input}
            >
              {formData.teamMembers.map((member, idx) => (
                <option key={idx} value={idx}>
                  {member.name || `Member ${idx + 1}`}
                </option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>Start Date:</label>
            <input
              type="date"
              value={newVacation.startDate}
              onChange={(e) => setNewVacation({ ...newVacation, startDate: e.target.value })}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>End Date:</label>
            <input
              type="date"
              value={newVacation.endDate}
              onChange={(e) => setNewVacation({ ...newVacation, endDate: e.target.value })}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Reason:</label>
            <input
              type="text"
              value={newVacation.reason}
              onChange={(e) => setNewVacation({ ...newVacation, reason: e.target.value })}
              style={styles.input}
            />
          </div>

          <button type="button" onClick={addVacation} style={styles.addBtn}>
            Add
          </button>
        </div>

        <h3>Sprint Holidays</h3>
        {formData.holidays.length > 0 && (
          <div style={styles.vacationsList}>
            {formData.holidays.map((holiday, idx) => (
              <div key={idx} style={styles.vacationItem}>
                <strong>{holiday.holidayDate}</strong>: {holiday.name}
                {holiday.description && ` - ${holiday.description}`}
                <button
                  type="button"
                  onClick={() => removeHoliday(idx)}
                  style={{ ...styles.removeBtn, marginLeft: '10px' }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <h4>Add Holiday</h4>
        <div style={styles.formRow}>
          <div style={styles.formGroup}>
            <label>Date:</label>
            <input
              type="date"
              value={newHoliday.holidayDate}
              onChange={(e) => setNewHoliday({ ...newHoliday, holidayDate: e.target.value })}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Name:</label>
            <input
              type="text"
              value={newHoliday.name}
              onChange={(e) => setNewHoliday({ ...newHoliday, name: e.target.value })}
              style={styles.input}
              placeholder="e.g., Christmas"
            />
          </div>

          <div style={styles.formGroup}>
            <label>Description (optional):</label>
            <input
              type="text"
              value={newHoliday.description}
              onChange={(e) => setNewHoliday({ ...newHoliday, description: e.target.value })}
              style={styles.input}
              placeholder="e.g., Public holiday"
            />
          </div>

          <button type="button" onClick={addHoliday} style={styles.addBtn}>
            Add Holiday
          </button>
        </div>

        <button type="submit" style={styles.submitBtn}>
          Create Sprint
        </button>
      </form>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1000px',
    margin: '0 auto',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
  },
  formRow: {
    display: 'flex',
    gap: '15px',
    alignItems: 'flex-end',
  },
  input: {
    padding: '8px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px',
  },
  memberCard: {
    padding: '15px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: '#f9f9f9',
  },
  addBtn: {
    padding: '8px 16px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    alignSelf: 'flex-start',
  },
  removeBtn: {
    padding: '4px 8px',
    backgroundColor: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  submitBtn: {
    padding: '12px',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
    marginTop: '20px',
  },
  holidayItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px',
    backgroundColor: '#f0f0f0',
    borderRadius: '4px',
  },
  vacationsList: {
    marginTop: '10px',
    padding: '8px',
    backgroundColor: '#fff',
    borderRadius: '4px',
  },
  vacationItem: {
    padding: '4px',
    fontSize: '12px',
  },
};

export default SprintForm;
