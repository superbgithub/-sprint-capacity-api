import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sprintService = {
  // Get all sprints
  getAllSprints: async (startDate = null, endDate = null) => {
    const params = {};
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;
    
    const response = await api.get('/sprints', { params });
    return response.data;
  },

  // Get sprint by ID
  getSprintById: async (sprintId) => {
    const response = await api.get(`/sprints/${sprintId}`);
    return response.data;
  },

  // Create new sprint
  createSprint: async (sprintData) => {
    const response = await api.post('/sprints', sprintData);
    return response.data;
  },

  // Update sprint
  updateSprint: async (sprintId, sprintData) => {
    const response = await api.put(`/sprints/${sprintId}`, sprintData);
    return response.data;
  },

  // Delete sprint
  deleteSprint: async (sprintId) => {
    await api.delete(`/sprints/${sprintId}`);
  },

  // Get capacity for sprint
  getSprintCapacity: async (sprintId) => {
    const response = await api.get(`/sprints/${sprintId}/capacity`);
    return response.data;
  },
};

export default api;
