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
import type { Event, ItineraryItem, OtherVenueShow } from './types';

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
  const [isPublishing, setIsPublishing] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [currentVoyageNumber, setCurrentVoyageNumber] = useState<string>('');
  const [shipVenues, setShipVenues] = useState<{ id: number; name: string }[]>([]);

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

  const [otherVenueShows, setOtherVenueShows] = useState<OtherVenueShow[]>([]);

  const [voyages, setVoyages] = useState<{ voyage_number: string; start_date: string; end_date: string }[]>([]);

  const [originalEvents, setOriginalEvents] = useState<Event[]>([]);
  const [originalItinerary, setOriginalItinerary] = useState<ItineraryItem[]>([]);
  const [isModified, setIsModified] = useState(false);

  // Check for modifications
  useEffect(() => {
    const eventsChanged = JSON.stringify(events) !== JSON.stringify(originalEvents);
    const itineraryChanged = JSON.stringify(itinerary) !== JSON.stringify(originalItinerary);
    setIsModified(eventsChanged || itineraryChanged);
  }, [events, itinerary, originalEvents, originalItinerary]);

  const loadShipVenues = async () => {
    try {
      const venues = await scheduleService.getShipVenues();
      setShipVenues(venues);
    } catch (error) {
      console.error("Failed to load ship venues", error);
    }
  };

  // Sync shipVenues with otherVenueShows to ensure template persistence
  useEffect(() => {
    if (shipVenues.length > 0) {
      setOtherVenueShows(prevShows => {
        const newShows = [...prevShows];
        let changed = false;

        shipVenues.forEach(venue => {
          if (!newShows.find(s => s.venue === venue.name)) {
            newShows.push({ venue: venue.name, shows: [] });
            changed = true;
          }
        });

        if (changed) {
          return newShows;
        }
        return prevShows;
      });
    }
  }, [shipVenues]);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await authService.validateToken();
      setUser(currentUser);
      if (currentUser) {
        loadVoyages();
        loadLatestSchedule();
        loadShipVenues();
      }
    } catch (error) {
      console.error("Auth check failed", error);
    } finally {
      setIsCheckingAuth(false);
    }
  };



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

    let processedEvents: Event[] = [];
    if (data.events && data.events.length > 0) {
      const newEvents: Event[] = data.events.map((e: any, index: number) => ({
        id: `loaded-${Date.now()}-${index}`,
        title: e.title,
        start: new Date(e.start),
        end: new Date(e.end),
        type: e.type || 'other',
        timeDisplay: e.time_display,
        notes: e.notes,
      }));
      processedEvents = assignEventColors(newEvents);
    }
    setEvents(processedEvents);
    setOriginalEvents(processedEvents);

    let processedItinerary: ItineraryItem[] = [];
    if (data.itinerary && data.itinerary.length > 0) {
      processedItinerary = data.itinerary.map((day: any) => ({
        day: day.day,
        date: day.date,
        location: day.location,
        time: formatTimeDisplay(day.arrival_time, day.departure_time) || day.port_times || '',
        arrival: day.arrival_time,
        departure: day.departure_time
      }));
    }
    setItinerary(processedItinerary);
    setOriginalItinerary(processedItinerary);

    // Process other venue shows
    const grouped: { [key: string]: { date: string; title: string; time: string }[] } = {};

    // Initialize with empty lists for all ship venues (template)
    shipVenues.forEach(v => {
      grouped[v.name] = [];
    });

    if (data.other_venue_shows && data.other_venue_shows.length > 0) {
      data.other_venue_shows.forEach((show: any) => {
        if (!grouped[show.venue]) {
          grouped[show.venue] = [];
        }
        grouped[show.venue].push({
          date: show.date,
          title: show.title,
          time: show.time
        });
      });
    }

    const newOtherShows: OtherVenueShow[] = Object.keys(grouped).map(venue => ({
      venue,
      shows: grouped[venue]
    }));
    setOtherVenueShows(newOtherShows);

    setIsModified(false);
  };

  const clearSchedule = () => {
    setEvents([]);
    setItinerary([]);
    setOriginalEvents([]);
    setOriginalItinerary([]);
    setCurrentVoyageNumber('');
    setIsModified(false);

    // Reset footer to template (empty rows for all venues)
    const templateShows: OtherVenueShow[] = shipVenues.map(v => ({
      venue: v.name,
      shows: []
    }));
    setOtherVenueShows(templateShows);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    clearSchedule();
    setVoyages([]);
    setShipVenues([]);
    setOtherVenueShows([]);
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
        setItinerary(newItinerary);
      }

      // Process other venue shows
      if (data.other_venue_shows && data.other_venue_shows.length > 0) {
        // Group by venue
        const grouped: { [key: string]: { date: string; title: string; time: string }[] } = {};

        data.other_venue_shows.forEach((show: any) => {
          if (!grouped[show.venue]) {
            grouped[show.venue] = [];
          }
          grouped[show.venue].push({
            date: show.date,
            title: show.title,
            time: show.time
          });
        });

        const newOtherShows: OtherVenueShow[] = Object.keys(grouped).map(venue => ({
          venue,
          shows: grouped[venue]
        }));
        setOtherVenueShows(newOtherShows);
      } else {
        setOtherVenueShows([]);
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
    try {
      setIsPublishing(true);
      await scheduleService.publishSchedule(voyageNumber, events, itinerary, otherVenueShows);
      setUploadSuccess(true);
      // Update current voyage number if it's new
      setCurrentVoyageNumber(voyageNumber);
      setIsModified(false);
      alert('Schedule published successfully!');
    } catch (error) {
      console.error("Failed to publish schedule", error);
      alert('Failed to publish schedule. Please try again.');
    } finally {
      // Update original state to match current state (reset modified status)
      setOriginalEvents(events);
      setOriginalItinerary(itinerary);
      setIsModified(false);

      loadVoyages();
      setIsPublishing(false);
    }
  };

  const handleDeleteSchedule = async (voyageNumber: string) => {
    await scheduleService.deleteSchedule(voyageNumber);
    alert(`Schedule for Voyage ${voyageNumber} deleted successfully.`);
    // Optionally clear events or reload
    clearSchedule();
    loadVoyages();
  };

  const handleDateChange = (dayIndex: number, newDate: Date) => {
    if (!itinerary[dayIndex]) return;

    // 1. Calculate the difference in days
    const oldDateStr = itinerary[dayIndex].date;
    const [oldYear, oldMonth, oldDay] = oldDateStr.split('-').map(Number);
    const oldDate = new Date(oldYear, oldMonth - 1, oldDay);

    // Reset hours to avoid timezone/DST issues affecting day calculation
    oldDate.setHours(0, 0, 0, 0);
    newDate.setHours(0, 0, 0, 0);

    const diffTime = newDate.getTime() - oldDate.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return;

    // 2. Shift Itinerary
    const newItinerary = itinerary.map(item => {
      const [y, m, d] = item.date.split('-').map(Number);
      const date = new Date(y, m - 1, d);
      date.setDate(date.getDate() + diffDays);

      // Format back to YYYY-MM-DD
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');

      return {
        ...item,
        date: `${year}-${month}-${day}`
      };
    });

    // 3. Shift Events
    const newEvents = events.map(event => {
      const newStart = new Date(event.start);
      newStart.setDate(newStart.getDate() + diffDays);

      const newEnd = new Date(event.end);
      newEnd.setDate(newEnd.getDate() + diffDays);

      return {
        ...event,
        start: newStart,
        end: newEnd
      };
    });

    setItinerary(newItinerary);
    setEvents(newEvents);
  };

  const handleLocationChange = (dayIndex: number, newLocation: string) => {
    const newItinerary = [...itinerary];
    if (newItinerary[dayIndex]) {
      newItinerary[dayIndex] = {
        ...newItinerary[dayIndex],
        location: newLocation
      };
      setItinerary(newItinerary);
    }
  };

  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/schedule" replace /> : <Login onLogin={(u) => { setUser(u); loadLatestSchedule(); loadVoyages(); loadShipVenues(); }} />
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
            isModified={isModified}
            onVoyageSelect={loadScheduleByVoyage}
            onNewSchedule={() => {
              clearSchedule();
              alert('Started a new schedule draft.');
            }}
          >
            <ScheduleGrid
              events={events}
              setEvents={setEvents}
              itinerary={itinerary}
              onDateChange={handleDateChange}
              onLocationChange={handleLocationChange}
              otherVenueShows={otherVenueShows}
            />

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
