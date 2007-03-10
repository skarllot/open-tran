create table locations (
	id integer primary key,
	project text not null
);

create table phrases (
	id integer primary key,
	phrase text not null,
	lang text not null,
	locationid int
);

create table canonical (
	id integer primary key,
	phrase text not null,
	lang text not null,
	locationid int
);

create table words (
	word text not null,
	canonicalid integer not null,
	count integer not null
);
