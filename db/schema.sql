drop table if exists posts;
create table posts (
  id integer primary key autoincrement,
  user text not null,
  poster text not null,
  value text not null,
  text text not null,
  posted_at timestamp not null
);