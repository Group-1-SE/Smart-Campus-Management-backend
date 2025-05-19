-- Create events table
CREATE TABLE events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name TEXT NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'active', 'expired')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create event_guest_vehicles table
CREATE TABLE event_guest_vehicles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    plate_number TEXT NOT NULL,
    name TEXT NOT NULL,
    reason TEXT,
    added_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_id, plate_number)
);

-- Create index for faster lookups
CREATE INDEX idx_event_guest_vehicles_event_id ON event_guest_vehicles(event_id);
CREATE INDEX idx_event_guest_vehicles_plate_number ON event_guest_vehicles(plate_number); 