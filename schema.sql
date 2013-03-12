drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  author_id string not null,
  gallery_id string not null,
  date timestamp not null,
  title string not null,
  descr string not null,
  filename string not null unique,
  size integer not null,
  mime integer not null
);