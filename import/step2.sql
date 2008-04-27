--  Copyright (C) 2007, 2008 Jacek Śliwerski (rzyjontko)
--
--  This program is free software; you can redistribute it and/or modify
--  it under the terms of the GNU General Public License as published by
--  the Free Software Foundation; version 2.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU General Public License for more details.
--
--  You should have received a copy of the GNU General Public License
--  along with this program; if not, write to the Free Software Foundation,
--  Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  


create table projects (
        id integer primary key,
	name text not null,
	url text
);


create table tlocations (
        projectid integer not null,
        phraseid integer not null,
        lang text not null
);


create table locations (
        projectid integer not null,
        phraseid integer not null,
        lang text not null,
        count integer not null
);


create table phrases (
        id integer primary key,
        phrase text not null,
        length int
);


create table words (
        word text not null,
        phraseid integer not null,
        count integer not null
);

