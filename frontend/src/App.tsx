import { useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { ScheduleGrid } from './components/Schedule/ScheduleGrid';
import { Modal } from './components/UI/Modal';
import { FileDropZone } from './components/Uploader/FileDropZone';
import { MockLogin } from './components/Auth/MockLogin';
import type { Event } from './components/Schedule/EventBlock';
import { startOfWeek, addDays, setHours, setMinutes } from 'date-fns';

function App() {
  const [user, setUser] = useState<{ name: string; role: string } | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const startDate = startOfWeek(new Date(), { weekStartsOn: 1 });

  const [events, setEvents] = useState<Event[]>([
    {
      id: '1',
      title: 'Oceanaria',
      start: setHours(setMinutes(addDays(startDate, 0), 0), 14),
      end: setHours(setMinutes(addDays(startDate, 0), 45), 15),
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
      <ScheduleGrid events={events} setEvents={setEvents} />

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
