import { useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { ScheduleGrid } from './components/Schedule/ScheduleGrid';
import { Modal } from './components/UI/Modal';
import { FileDropZone } from './components/Uploader/FileDropZone';
import { MockLogin } from './components/Auth/MockLogin';
import type { Event, ItineraryItem } from './types';

function App() {
  const [user, setUser] = useState<{ name: string; role: string } | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

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

  if (!user) {
    return <MockLogin onLogin={setUser} />;
  }

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload/cd-grid', {
        method: 'POST',
        body: formData,
      });

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
      setIsImportOpen(false);

      alert(`Successfully imported ${newEvents.length} events across ${data.itinerary?.length || 0} days!`);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <MainLayout onImportClick={() => setIsImportOpen(true)} user={user}>
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
        />
      </Modal>
    </MainLayout>
  );
}

export default App;
