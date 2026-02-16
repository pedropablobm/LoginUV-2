-- 02. Modelo de datos inicial

CREATE TABLE campuses (
  id SERIAL PRIMARY KEY,
  code VARCHAR(30) UNIQUE NOT NULL,
  name VARCHAR(120) NOT NULL,
  is_main BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE labs (
  id SERIAL PRIMARY KEY,
  campus_id INT NOT NULL REFERENCES campuses(id),
  code VARCHAR(30) NOT NULL,
  name VARCHAR(120) NOT NULL,
  UNIQUE (campus_id, code)
);

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(60) UNIQUE NOT NULL,
  full_name VARCHAR(160) NOT NULL,
  email VARCHAR(180),
  role VARCHAR(20) NOT NULL CHECK (role IN ('student','teacher','admin')),
  academic_plan VARCHAR(120),
  semester VARCHAR(20),
  password_hash TEXT NOT NULL,
  allow_multi_session BOOLEAN NOT NULL DEFAULT FALSE,
  max_sessions SMALLINT NOT NULL DEFAULT 1,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  source VARCHAR(20) NOT NULL DEFAULT 'local',
  glpi_external_id VARCHAR(80),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE machines (
  id BIGSERIAL PRIMARY KEY,
  campus_id INT NOT NULL REFERENCES campuses(id),
  lab_id INT NOT NULL REFERENCES labs(id),
  hostname VARCHAR(80) UNIQUE NOT NULL,
  asset_tag VARCHAR(80),
  os_type VARCHAR(20) NOT NULL CHECK (os_type IN ('windows','debian')),
  status VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (status IN ('free','occupied','offline','maintenance')),
  last_seen_at TIMESTAMPTZ,
  glpi_external_id VARCHAR(80),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  machine_id BIGINT NOT NULL REFERENCES machines(id),
  auth_mode VARCHAR(20) NOT NULL CHECK (auth_mode IN ('central','relay')),
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','closed','forced')),
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ,
  close_reason VARCHAR(30) CHECK (close_reason IN ('logout','shutdown','unexpected_shutdown','admin_force','timeout')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  campus_id INT REFERENCES campuses(id),
  lab_id INT REFERENCES labs(id),
  user_id BIGINT REFERENCES users(id),
  machine_id BIGINT REFERENCES machines(id),
  session_id BIGINT REFERENCES sessions(id),
  event_type VARCHAR(40) NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE csv_imports (
  id BIGSERIAL PRIMARY KEY,
  imported_by BIGINT REFERENCES users(id),
  filename VARCHAR(200) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('processing','success','partial','failed')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  summary JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE csv_import_rows (
  id BIGSERIAL PRIMARY KEY,
  import_id BIGINT NOT NULL REFERENCES csv_imports(id) ON DELETE CASCADE,
  row_number INT NOT NULL,
  row_status VARCHAR(20) NOT NULL CHECK (row_status IN ('ok','error','skipped')),
  error_message TEXT,
  raw_data JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE glpi_sync_runs (
  id BIGSERIAL PRIMARY KEY,
  run_type VARCHAR(20) NOT NULL CHECK (run_type IN ('manual','scheduled')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('processing','success','partial','failed')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  summary JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX idx_sessions_machine_status ON sessions(machine_id, status);
CREATE INDEX idx_events_created_at ON events(created_at DESC);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_machines_lab_status ON machines(lab_id, status);
