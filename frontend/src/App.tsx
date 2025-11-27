import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { MainLayout } from './components/Layout/MainLayout';
import { ScheduleGrid } from './components/Schedule/ScheduleGrid';
import { Modal } from './components/UI/Modal';
import { FileDropZone } from './components/Uploader/FileDropZone';
import { Login } from './components/Auth/Login';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { authService } from './services/authService';
import { scheduleService } from './services/scheduleService';
import type { Event, ItineraryItem } from './types';

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState<{ name: string; role: string; username: string; venueName?: string } | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [currentVoyageNumber, setCurrentVoyageNumber] = useState<string>('');

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
        loadLatestSchedule();
      }
      setIsCheckingAuth(false);
    };

    restoreSession();
  }, []);

  const loadLatestSchedule = async () => {
    try {
      const data = await scheduleService.getLatestSchedule();
      if (data.voyage_number) {
        setCurrentVoyageNumber(data.voyage_number);
      }
      if (data.events && data.events.length > 0) {
        const newEvents: Event[] = data.events.map((e: any, index: number) => ({
          id: `loaded-${Date.now()}-${index}`,
          title: e.title,
          start: new Date(e.start),
          end: new Date(e.end),
          type: e.type || 'other',
          notes: e.notes,
          color: e.color,
        }));
        setEvents(newEvents);
      }

      if (data.itinerary && data.itinerary.length > 0) {
        const newItinerary: ItineraryItem[] = data.itinerary.map((day: any) => ({
          day: day.day,
          date: day.date,
          location: day.location,
          time: day.port_times || ''
        }));
        setItinerary(newItinerary);
      } else {
        // Clear itinerary if none found
        setItinerary([]);
      }

      if (!data.events || data.events.length === 0) {
        setEvents([]);
      }
      if (!data.voyage_number) {
        setCurrentVoyageNumber('');
      }

    } catch (error) {
      console.error("Failed to load latest schedule", error);
      // Ensure state is cleared on error or empty
      setEvents([]);
      setItinerary([]);
      setCurrentVoyageNumber('');
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setEvents([]);
    setItinerary([]);
    setCurrentVoyageNumber('');
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
        color: e.color,
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
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Please try again.');
      setIsUploading(false);
    }
  };

  const handleViewSchedule = () => {
    setIsImportOpen(false);
    setIsUploading(false);
    setUploadSuccess(false);
  };

  const handlePublishSchedule = async (voyageNumber: string) => {
    await scheduleService.publishSchedule(voyageNumber, events, itinerary);
    alert(`Schedule for Voyage ${voyageNumber} published successfully!`);
  };

  const handleDeleteSchedule = async (voyageNumber: string) => {
    await scheduleService.deleteSchedule(voyageNumber);
    alert(`Schedule for Voyage ${voyageNumber} deleted successfully.`);
    // Optionally clear events or reload
    setEvents([]);
    // setItinerary([]); // Maybe keep itinerary?
  };

  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/schedule" replace /> : <Login onLogin={(u) => { setUser(u); loadLatestSchedule(); }} />
      } />

      <Route path="/schedule" element={
        <ProtectedRoute user={user}>
          <MainLayout
            onImportClick={() => setIsImportOpen(true)}
            onLogout={handleLogout}
            user={user}
            onPublish={handlePublishSchedule}
            onDelete={handleDeleteSchedule}
            currentVoyageNumber={currentVoyageNumber}
          >
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
