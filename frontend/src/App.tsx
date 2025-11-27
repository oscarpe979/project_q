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
import { assignEventColors } from './utils/eventColors';
import type { Event, ItineraryItem } from './types';

function formatTimeDisplay(arrival?: string, departure?: string): string {
  const formatSingleTime = (t?: string) => {
    if (!t || t.toLowerCase() === 'null') return null;
    // Try parsing 24h time "17:00" -> "5:00 pm"
    const [hours, minutes] = t.split(':').map(Number);
    if (!isNaN(hours) && !isNaN(minutes)) {
      const date = new Date();
      date.setHours(hours, minutes);
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).toLowerCase();
    }
    return t; // Return as is if not HH:MM
  };

  const arr = formatSingleTime(arrival);
  const dep = formatSingleTime(departure);

  if (arr && dep) return `${arr} - ${dep}`;
  if (arr) return `Arrival ${arr}`;
  if (dep) return `Departure ${dep}`;
  return '';
}

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

  const [voyages, setVoyages] = useState<{ voyage_number: string; start_date: string; end_date: string }[]>([]);

  // Session restoration on app load
  useEffect(() => {
    const restoreSession = async () => {
      const userData = await authService.validateToken();
      if (userData) {
        setUser(userData);
        loadLatestSchedule();
        loadVoyages();
      }
      setIsCheckingAuth(false);
    };

    restoreSession();
  }, []);

  const loadVoyages = async () => {
    try {
      const data = await scheduleService.getVoyages();
      setVoyages(data);
    } catch (error) {
      console.error("Failed to load voyages", error);
    }
  };

  const loadLatestSchedule = async () => {
    try {
      const data = await scheduleService.getLatestSchedule();
      processScheduleData(data);
    } catch (error) {
      console.error("Failed to load latest schedule", error);
      clearSchedule();
    }
  };

  const loadScheduleByVoyage = async (voyageNumber: string) => {
    try {
      const data = await scheduleService.getScheduleByVoyage(voyageNumber);
      processScheduleData(data);
    } catch (error) {
      console.error("Failed to load schedule", error);
      alert('Failed to load schedule');
    }
  };

  const processScheduleData = (data: any) => {
    if (data.voyage_number) {
      setCurrentVoyageNumber(data.voyage_number);
    } else {
      setCurrentVoyageNumber('');
    }
    if (data.events && data.events.length > 0) {
      const newEvents: Event[] = data.events.map((e: any, index: number) => ({
        id: `loaded-${Date.now()}-${index}`,
        title: e.title,
        start: new Date(e.start),
        end: new Date(e.end),
        type: e.type || 'other',
        notes: e.notes,
      }));
      const coloredEvents = assignEventColors(newEvents);
      setEvents(coloredEvents);
    } else {
      setEvents([]);
    }

    if (data.itinerary && data.itinerary.length > 0) {
      const newItinerary: ItineraryItem[] = data.itinerary.map((day: any) => ({
        day: day.day,
        date: day.date,
        location: day.location,
        time: formatTimeDisplay(day.arrival_time, day.departure_time) || day.port_times || '',
        arrival: day.arrival_time,
        departure: day.departure_time
      }));
      setItinerary(newItinerary);
    } else {
      setItinerary([]);
    }
  };

  const clearSchedule = () => {
    setEvents([]);
    setItinerary([]);
    setCurrentVoyageNumber('');
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    clearSchedule();
    setVoyages([]);
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
      }));

      // Apply colors using frontend utility
      const coloredEvents = assignEventColors(newEvents);

      // Transform and update itinerary
      if (data.itinerary && data.itinerary.length > 0) {
        const newItinerary: ItineraryItem[] = data.itinerary.map((day: any) => ({
          day: day.day_number,
          date: day.date,
          location: day.port,
          time: formatTimeDisplay(day.arrival_time, day.departure_time),
          arrival: day.arrival_time,
          departure: day.departure_time
        }));
        setItinerary(newItinerary);
      }

      setEvents(prev => [...prev, ...coloredEvents]);
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
    setCurrentVoyageNumber(voyageNumber);
    loadVoyages();
    alert(`Schedule for Voyage ${voyageNumber} published successfully!`);
  };

  const handleDeleteSchedule = async (voyageNumber: string) => {
    await scheduleService.deleteSchedule(voyageNumber);
    alert(`Schedule for Voyage ${voyageNumber} deleted successfully.`);
    // Optionally clear events or reload
    setEvents([]);
    setItinerary([]);
    setCurrentVoyageNumber('');
    loadVoyages();
  };

  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/schedule" replace /> : <Login onLogin={(u) => { setUser(u); loadLatestSchedule(); loadVoyages(); }} />
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
            voyages={voyages}
            onVoyageSelect={loadScheduleByVoyage}
            onNewSchedule={() => {
              clearSchedule();
              alert('Started a new schedule draft.');
            }}
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
