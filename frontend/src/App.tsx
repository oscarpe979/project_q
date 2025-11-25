import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { MainLayout } from './components/Layout/MainLayout';
import { ScheduleGrid } from './components/Schedule/ScheduleGrid';
import { Modal } from './components/UI/Modal';
import { FileDropZone } from './components/Uploader/FileDropZone';
import { Login } from './components/Auth/Login';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { authService } from './services/authService';
import type { Event, ItineraryItem } from './types';

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState<{ name: string; role: string; username: string; venueName?: string } | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  const [itinerary, setItinerary] = useState<ItineraryItem[]>([
    { day: 1, date: '2025-11-17', location: 'SHANGHAI', time: '7:00 am - 4:30 pm' },
    { day: 2, date: '2025-11-18', location: 'AT SEA', time: '' },
    { day: 3, date: '2025-11-19', location: 'BUSAN', time: '7:00 am - 7:00 pm' },
    { day: 4, date: '2025-11-20', location: 'FUKUOKA', time: '7:00 am - 6:00 pm' },
    { day: 5, date: '2025-11-21', location: 'AT SEA', time: '' },
    { day: 6, date: '2025-11-22', location: 'NAGASAKI', time: '7:00 am - 5:00 pm' },
    { day: 7, date: '2025-11-23', location: 'AT SEA', time: '' },
  ]);

  const [events, setEvents] = useState<Event[]>([
    {
      id: '1',
      title: 'Oceanaria',
      start: new Date(2025, 10, 18, 0, 0), // Nov 17, 2025 at 2:00 PM
      end: new Date(2025, 10, 18, 1, 0),   // Nov 17, 2025 at 3:45 PM
      type: 'show',
    },
  ]);

  // Session restoration on app load
  useEffect(() => {
    const restoreSession = async () => {
      const userData = await authService.validateToken();
      if (userData) {
        setUser(userData);
      }
      setIsCheckingAuth(false);
    };

    restoreSession();
  }, []);

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    navigate('/login');
  };

  if (isCheckingAuth) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    setUploadSuccess(false);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const headers = authService.getAuthHeaders();
      // headers is HeadersInit, but fetch expects HeadersInit. 
      // We need to cast or construct properly if it's a simple object.
      // authService returns { Authorization: ... } which is valid.

      const response = await fetch('http://localhost:8000/api/upload/cd-grid', {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (response.status === 401) {
        authService.removeToken();
        setUser(null);
        navigate('/login');
        throw new Error('Session expired. Please login again.');
      }

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      console.log("Received Data from Backend:", data);

      // Transform backend events to frontend format
      const newEvents: Event[] = data.events.map((e: any, index: number) => ({
        id: `imported-${Date.now()}-${index}`,
        title: e.title,
        start: new Date(e.start),
        end: new Date(e.end),
        type: e.type || 'other',
      }));

      // Transform and update itinerary
      if (data.itinerary && data.itinerary.length > 0) {
        const newItinerary: ItineraryItem[] = data.itinerary.map((day: any) => ({
          day: day.day_number,
          date: day.date,
          location: day.port,
          time: day.port_times || ''
        }));
        setItinerary(newItinerary);
      }

      setEvents(prev => [...prev, ...newEvents]);
      setUploadSuccess(true);
      // setIsImportOpen(false); // Don't close immediately
      // alert(`Successfully imported ${newEvents.length} events across ${data.itinerary?.length || 0} days!`);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Please try again.');
      setIsUploading(false); // Only stop uploading on error, success is handled by UI
    }
  };

  const handleViewSchedule = () => {
    setIsImportOpen(false);
    setIsUploading(false);
    setUploadSuccess(false);
  };

  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/schedule" replace /> : <Login onLogin={setUser} />
      } />

      <Route path="/schedule" element={
        <ProtectedRoute user={user}>
          <MainLayout onImportClick={() => setIsImportOpen(true)} onLogout={handleLogout} user={user}>
            <ScheduleGrid events={events} setEvents={setEvents} itinerary={itinerary} />

            <Modal
              isOpen={isImportOpen}
              onClose={() => !isUploading && setIsImportOpen(false)}
              title="Import Schedule Grid"
            >
              <FileDropZone
                onFileSelect={handleFileSelect}
                accept=".pdf,.xlsx,.xls"
                isLoading={isUploading}
                isSuccess={uploadSuccess}
                onViewSchedule={handleViewSchedule}
              />
            </Modal>
          </MainLayout>
        </ProtectedRoute>
      } />

      <Route path="/" element={<Navigate to="/schedule" replace />} />
    </Routes>
  );
}

export default App;
