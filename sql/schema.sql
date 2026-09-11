CREATE TABLE gyms (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL,
 state TEXT NOT NULL, neighborhood TEXT NOT NULL, address TEXT NOT NULL, latitude REAL NOT NULL,
 longitude REAL NOT NULL, opening_hours TEXT NOT NULL, search_text TEXT NOT NULL
);
CREATE INDEX gyms_state ON gyms(state);
CREATE TABLE profiles (
 weekday INTEGER CHECK(weekday BETWEEN 0 AND 6),
 hour INTEGER CHECK(hour BETWEEN 0 AND 23),
 score INTEGER CHECK(score BETWEEN 0 AND 100),
 samples INTEGER NOT NULL, PRIMARY KEY(weekday,hour)
);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE benefits (
 gym_id TEXT NOT NULL REFERENCES gyms(id),
 provider TEXT CHECK(provider IN ('wellhub','totalpass')),
 status TEXT CHECK(status IN ('yes','no','unknown')),
 source_url TEXT NOT NULL, checked_at TEXT NOT NULL,
 PRIMARY KEY(gym_id,provider)
);
