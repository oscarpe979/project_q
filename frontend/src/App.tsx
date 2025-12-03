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
import type { Event, ItineraryItem, OtherVenueShow, HistoryState } from './types';

function formatTimeDisplay(arrival?: string, departure?: string): string {
  const formatSingleTime = (t?: string) => {
    if (!t || t.trim().toLowerCase() === 'null') return null;
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
  const [shipVenues, setShipVenues] = useState<{ id: number; name: string }[]>([]);
  const [processingTime, setProcessingTime] = useState<string | null>(null);

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
  const [originalOtherVenueShows, setOriginalOtherVenueShows] = useState<OtherVenueShow[]>([]);
  const [isModified, setIsModified] = useState(false);

  // Undo/Redo State
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const MAX_HISTORY = 30;

  // Helper to add to history
  const addToHistory = (newState: HistoryState) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      const updatedHistory = [...newHistory, newState];
      if (updatedHistory.length > MAX_HISTORY) {
        updatedHistory.shift();
      }
      return updatedHistory;
    });
    setHistoryIndex(prev => Math.min(prev + 1, MAX_HISTORY - 1));
  };

  // Initialize history when data is loaded or reset
  const initializeHistory = (initialEvents: Event[], initialItinerary: ItineraryItem[], initialShows: OtherVenueShow[]) => {
    const initialState: HistoryState = {
      events: JSON.parse(JSON.stringify(initialEvents)),
      itinerary: JSON.parse(JSON.stringify(initialItinerary)),
      otherVenueShows: JSON.parse(JSON.stringify(initialShows))
    };
    setHistory([initialState]);
    setHistoryIndex(0);
  };

  // Effect to initialize history on first load if empty
  useEffect(() => {
    if (history.length === 0 && events.length > 0) {
      initializeHistory(events, itinerary, otherVenueShows);
    }
  }, []); // Run once on mount, but we also handle resets manually in load functions

  const undo = () => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      // Restore state without triggering addToHistory
      // We need to be careful not to trigger effects that might add to history again if we were using a different pattern
      // But here we will manually set state.
      // NOTE: Dates need to be reconstructed from JSON if we used JSON.stringify/parse for deep copy, 
      // but here we might need a better deep copy or just handle dates.
      // Let's fix the Date objects for events.
      const restoredEvents = prevState.events.map(e => ({
        ...e,
        start: new Date(e.start),
        end: new Date(e.end)
      }));

      setEvents(restoredEvents);
      setItinerary(prevState.itinerary);
      setOtherVenueShows(prevState.otherVenueShows);
      setHistoryIndex(prev => prev - 1);
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      const restoredEvents = nextState.events.map(e => ({
        ...e,
        start: new Date(e.start),
        end: new Date(e.end)
      }));

      setEvents(restoredEvents);
      setItinerary(nextState.itinerary);
      setOtherVenueShows(nextState.otherVenueShows);
      setHistoryIndex(prev => prev + 1);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        undo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        redo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [history, historyIndex]); // Re-bind when history changes

  // Check for modifications
  // Check for modifications
  useEffect(() => {
    const eventsChanged = !areEventsEqual(events, originalEvents);
    const itineraryChanged = JSON.stringify(itinerary) !== JSON.stringify(originalItinerary);
    const otherShowsChanged = JSON.stringify(otherVenueShows) !== JSON.stringify(originalOtherVenueShows);
    setIsModified(eventsChanged || itineraryChanged || otherShowsChanged);
  }, [events, itinerary, otherVenueShows, originalEvents, originalItinerary, originalOtherVenueShows]);

  // Helper to check if events are equal
  const areEventsEqual = (arr1: Event[], arr2: Event[]) => {
    if (arr1.length !== arr2.length) return false;
    // Sort by ID to ensure order doesn't matter for comparison
    const sorted1 = [...arr1].sort((a, b) => a.id.localeCompare(b.id));
    const sorted2 = [...arr2].sort((a, b) => a.id.localeCompare(b.id));

    return sorted1.every((e1, i) => {
      const e2 = sorted2[i];
      return (
        e1.id === e2.id &&
        e1.title === e2.title &&
        e1.start.getTime() === e2.start.getTime() &&
        e1.end.getTime() === e2.end.getTime() &&
        e1.type === e2.type &&
        e1.color === e2.color &&
        e1.notes === e2.notes &&
        (e1.timeDisplay === e2.timeDisplay || (!e1.timeDisplay && !e2.timeDisplay))
      );
    });
  };

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
        arrival: (day.arrival_time && day.arrival_time.trim().toLowerCase() !== 'null') ? day.arrival_time : null,
        departure: (day.departure_time && day.departure_time.trim().toLowerCase() !== 'null') ? day.departure_time : null
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
    setOriginalOtherVenueShows(JSON.parse(JSON.stringify(newOtherShows)));

    setIsModified(false);
    initializeHistory(processedEvents, processedItinerary, newOtherShows);
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
    initializeHistory([], [], templateShows);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    clearSchedule();
    setVoyages([]);
    setShipVenues([]);
    setOtherVenueShows([]);
    setIsUploading(false);
    setUploadSuccess(false);
    navigate('/login');
  };

  if (isCheckingAuth) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    setUploadSuccess(false);
    setProcessingTime(null);
    const startTime = Date.now();
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
          arrival: (day.arrival_time && day.arrival_time.trim().toLowerCase() !== 'null') ? day.arrival_time : null,
          departure: (day.departure_time && day.departure_time.trim().toLowerCase() !== 'null') ? day.departure_time : null
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

      const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
      const mins = Math.floor(durationSeconds / 60);
      const secs = durationSeconds % 60;
      const formattedTime = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

      setProcessingTime(formattedTime);
      setIsUploading(false);
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
      setOriginalOtherVenueShows(otherVenueShows);
      setIsModified(false);

      loadVoyages();
    }
  };

  const handleDeleteSchedule = async (voyageNumber: string) => {
    await scheduleService.deleteSchedule(voyageNumber);
    alert(`Schedule for Voyage ${voyageNumber} deleted successfully.`);
    // Optionally clear events or reload
    clearSchedule();
    loadVoyages();
  };



  // Wrapped Setters
  const handleEventsChange = (newEvents: Event[] | ((prev: Event[]) => Event[])) => {
    // Calculate new state based on current 'events' from closure
    // This avoids side effects inside the setState updater
    const updatedEvents = typeof newEvents === 'function' ? newEvents(events) : newEvents;

    // Check if events actually changed
    if (areEventsEqual(events, updatedEvents)) {
      return;
    }

    setEvents(updatedEvents);

    // Add to history
    addToHistory({
      events: JSON.parse(JSON.stringify(updatedEvents)), // Deep copy to avoid reference issues
      itinerary: JSON.parse(JSON.stringify(itinerary)),
      otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
    });
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

    // 4. Shift Other Venue Shows
    const newOtherVenueShows = otherVenueShows.map(venue => ({
      ...venue,
      shows: venue.shows.map(show => {
        const [y, m, d] = show.date.split('-').map(Number);
        const date = new Date(y, m - 1, d);
        date.setDate(date.getDate() + diffDays);

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');

        return {
          ...show,
          date: `${year}-${month}-${day}`
        };
      })
    }));

    setItinerary(newItinerary);
    setEvents(newEvents);
    setOtherVenueShows(newOtherVenueShows);

    addToHistory({
      events: JSON.parse(JSON.stringify(newEvents)),
      itinerary: JSON.parse(JSON.stringify(newItinerary)),
      otherVenueShows: JSON.parse(JSON.stringify(newOtherVenueShows))
    });
  };

  const handleLocationChange = (dayIndex: number, newLocation: string) => {
    const newItinerary = [...itinerary];
    if (newItinerary[dayIndex]) {
      newItinerary[dayIndex] = {
        ...newItinerary[dayIndex],
        location: newLocation
      };
      setItinerary(newItinerary);

      addToHistory({
        events: JSON.parse(JSON.stringify(events)),
        itinerary: JSON.parse(JSON.stringify(newItinerary)),
        otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
      });
    }
  };



  const handleTimeChange = (dayIndex: number, arrival: string | null, departure: string | null) => {
    const newItinerary = [...itinerary];
    if (newItinerary[dayIndex]) {
      // Format the display time string
      const timeDisplay = formatTimeDisplay(arrival || undefined, departure || undefined);

      newItinerary[dayIndex] = {
        ...newItinerary[dayIndex],
        arrival: arrival || undefined,
        departure: departure || undefined,
        time: timeDisplay
      };
      setItinerary(newItinerary);

      addToHistory({
        events: JSON.parse(JSON.stringify(events)),
        itinerary: JSON.parse(JSON.stringify(newItinerary)),
        otherVenueShows: JSON.parse(JSON.stringify(otherVenueShows))
      });

      setIsModified(true);
    }
  };

  const handleOtherVenueShowUpdate = (venue: string, date: string, title: string, time: string) => {
    const newShows = [...otherVenueShows];
    const venueIndex = newShows.findIndex(v => v.venue === venue);

    if (venueIndex !== -1) {
      const currentShows = newShows[venueIndex].shows;
      const showIndex = currentShows.findIndex(s => s.date === date);
      const existingShow = showIndex !== -1 ? currentShows[showIndex] : null;

      // Check if values actually changed
      const currentTitle = existingShow ? existingShow.title : '';
      const currentTime = existingShow ? existingShow.time : '';

      if (currentTitle === title && currentTime === time) {
        return; // No change, do nothing
      }

      // Deep copy the venue object we are modifying
      newShows[venueIndex] = { ...newShows[venueIndex], shows: [...newShows[venueIndex].shows] };

      if (title.trim() === '' && time.trim() === '') {
        // Delete if both empty
        if (showIndex !== -1) {
          newShows[venueIndex].shows.splice(showIndex, 1);
        }
      } else {
        // Update or Add
        if (showIndex !== -1) {
          newShows[venueIndex].shows[showIndex] = { date, title, time };
        } else {
          newShows[venueIndex].shows.push({ date, title, time });
        }
      }
    }

    setOtherVenueShows(newShows);

    addToHistory({
      events: JSON.parse(JSON.stringify(events)),
      itinerary: JSON.parse(JSON.stringify(itinerary)),
      otherVenueShows: JSON.parse(JSON.stringify(newShows))
    });

    setIsModified(true);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}


      <Routes>
        <Route path="/login" element={
          user ? <Navigate to="/schedule" replace /> : <Login onLogin={(u) => { setUser(u); loadLatestSchedule(); loadVoyages(); loadShipVenues(); }} />
        } />

        <Route path="/schedule" element={
          <ProtectedRoute user={user}>
            <MainLayout
              onImportClick={() => {
                setUploadSuccess(false);
                setProcessingTime(null);
                setIsUploading(false);
                setIsImportOpen(true);
              }}
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
              undo={undo}
              redo={redo}
              canUndo={historyIndex > 0}
              canRedo={historyIndex < history.length - 1}
            >
              <ScheduleGrid
                events={events}
                setEvents={handleEventsChange}
                itinerary={itinerary}
                onDateChange={handleDateChange}
                onLocationChange={handleLocationChange}
                onTimeChange={handleTimeChange}
                otherVenueShows={otherVenueShows}
                onOtherVenueShowUpdate={handleOtherVenueShowUpdate}
              />
            </MainLayout>
          </ProtectedRoute>
        } />

        <Route path="/" element={<Navigate to="/schedule" replace />} />
      </Routes>

      {/* Import Modal */}
      <Modal
        isOpen={isImportOpen}
        onClose={() => !isUploading && setIsImportOpen(false)}
        title="Import Schedule"
      >
        {uploadSuccess ? (
          <div className="processing-status-container success">
            <div className="success-icon-wrapper">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M22 4L12 14.01l-3-3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h3 className="success-title">Import Successful!</h3>
            <p className="success-message">
              Schedule for Voyage {currentVoyageNumber} has been successfully imported and processed.
              {processingTime && <span style={{ display: 'block', marginTop: '8px', fontSize: '0.9em', opacity: 0.8 }}>Processed in {processingTime}</span>}
            </p>
            <button
              className="view-schedule-btn"
              onClick={() => {
                setIsImportOpen(false);
              }}
            >
              View Schedule
            </button>
          </div>
        ) : (
          <FileDropZone
            onFileSelect={handleFileSelect}
            isLoading={isUploading}
          />
        )}
      </Modal>
    </div>
  );
}

export default App;
