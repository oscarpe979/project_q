# Royal Caribbean Venue Scheduler - MVP Walkthrough

This document outlines the features implemented in the MVP version of the Venue Scheduler application.

## Features Implemented

### 1. Core UI & Design
- **Premium Glass Aesthetic**: A sophisticated light theme with refined glassmorphism, gradients, and shadows, implemented using **Vanilla CSS**.
- **Main Layout**: Integrated sidebar with brand identity, user profile, and a sticky header.
- **Schedule Grid**: A polished, spacious view with sticky headers, subtle grid lines, and a "Google Calendar" feel.

### 2. Interactive Scheduling
- **Drag and Drop**: Move events between days and times by dragging them.
- **Resizing**: Adjust event duration by dragging the bottom handle of an event block.
- **Smart Stacking**: Overlapping events automatically adjust their width and position to avoid visual clutter.

### 3. Data Import
- **File Upload**: Import "CD Grids" via the "Import Grid" button in the sidebar.
- **PDF Support**: Parses standard CD Grid PDFs (extracts dates and events).
- **Excel Support**: Parses CD Grid Excel files (`.xls`, `.xlsx`).

### 4. Mock Authentication
- **Login Screen**: A simulated login screen to choose a role (Stage Manager, Production Manager, etc.).
- **User Profile**: Displays the logged-in user's initials and role in the sidebar.

## How to Run

### Backend
1. Navigate to the project root.
2. Start the FastAPI server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

## Testing the Workflow
1. **Login**: Select a role (e.g., "Stage Manager") and click "Enter Demo Mode".
2. **View Schedule**: You will see a sample schedule populated with mock data.
3. **Interact**: Try dragging events to different times or resizing them.
4. **Import**:
   - Click "Import Grid" in the sidebar.
   - Drag and drop one of the sample files from `docs/` (e.g., `CD Grid Example 1.pdf` or `Two70 Schedule Excel 1.xls`).
   - The events from the file will be parsed and added to the schedule.

## Next Steps
- Implement "AM Grid" specific parsing if different from CD Grid.
- Implement Export functionality (Excel/PDF).
- Connect to a real database (PostgreSQL).
