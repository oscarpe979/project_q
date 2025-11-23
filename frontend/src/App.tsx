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
      start: new Date(2025, 10, 17, 14, 0), // Nov 17, 2025 at 2:00 PM
      end: new Date(2025, 10, 17, 15, 45),   // Nov 17, 2025 at 3:45 PM
      type: 'show',
    },
  ]);

  if (!user) {
    return <MockLogin onLogin={setUser} />;
  }

  const handleFileSelect = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload/cd-grid', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();

      // Transform backend events to frontend format
      const newEvents: Event[] = data.events.map((e: any, index: number) => ({
        id: `imported-${index}`,
        title: e.title,
        start: new Date(e.start),
        end: new Date(e.end),
        type: e.type || 'other',
      }));

      setEvents(prev => [...prev, ...newEvents]);
      setIsImportOpen(false);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    }
  };

  return (
    <MainLayout onImportClick={() => setIsImportOpen(true)} user={user}>
      <ScheduleGrid events={events} setEvents={setEvents} itinerary={itinerary} />

      <Modal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        title="Import Schedule Grid"
      >
        <FileDropZone onFileSelect={handleFileSelect} accept=".pdf,.xlsx,.xls" />
      </Modal>
    </MainLayout>
  );
}

export default App;
