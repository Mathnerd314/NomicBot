CREATE TABLE settings
  (setting_name TEXT PRIMARY KEY, setting_value TEXT);

INSERT INTO settings
VALUES
  ('prefix', '!'),
  ('manageUsers'   , '[]'),
  ('manageRoles'   , '[]'),
  ('disabled'      , 'False'),
  ('name', 'NomicBot'),
  ('activeChannels','[1414231231]'),
  ('logChannel','1414231232'),
  ('discordToken', '');

CREATE TABLE callbacks
  (timestamp INT, callback TEXT);
