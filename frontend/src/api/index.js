import axios from 'axios';

const API_BASE = 'http://localhost:8005';

const api = axios.create({
    baseURL: API_BASE,
});

// Set token for sub-sequent requests
export const setAuthToken = (token) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete api.defaults.headers.common['Authorization'];
    }
};

export const fetchStats = async () => {
    const response = await api.get('/stats');
    return response.data;
};

export const fetchViolations = async () => {
    const response = await api.get('/violations');
    return response.data;
};

export const switchCamera = async (source) => {
    const response = await api.post('/switch_camera', { source });
    return response.data;
};

export const uploadMedia = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getStreamUrl = () => `${API_BASE}/video_feed`;
export const getViolationVideoUrl = (filename) => `${API_BASE}/video/violation/${filename}`;
