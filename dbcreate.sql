-- Copyright (C) 2007 Alex Drummond <a.d.drummond@gmail.com>
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 51 Franklin Street, Fifth Floor,
-- Boston, MA  02110-1301, USA.

--
-- This script creates all the tables in the database.
--

CREATE TABLE wikiusers
(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT, -- Password is NULL for anon users.
    email TEXT UNIQUE
);

CREATE TABLE articles
(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    -- Either redirect is NULL and cached_xhtml is non-null,
    -- or redirect is non-null and cached_xhtml is null.
    redirect TEXT,
    source TEXT,
    cached_xhtml,
    title TEXT NOT NULL
);

-- NOTE: These are NOT discussion threads. A thread is a tag used to identify
-- articles through all the revisions they go through.
CREATE TABLE threads
(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE category_specs
(
    threads_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (threads_id) REFERENCES threads(id),
    PRIMARY KEY (threads_id, name)
);

CREATE TABLE wikiusers_prefs
(
    wikiusers_id INTEGER NOT NULL PRIMARY KEY,
    -- Should we email changes on the user's watchlist to him?
    email_changes BOOLEAN NOT NULL,
    -- If so, should we email each change individually or do it in digest
    -- form?
    digest BOOLEAN NOT NULL
);

CREATE TABLE watchlist_items
(
    wikiusers_id INTEGER NOT NULL,
    threads_id INTEGER NOT NULL,
    FOREIGN KEY (wikiusers_id) REFERENCES wikiusers(id),
    FOREIGN KEY (threads_id) REFERENCES threads(id),
    PRIMARY KEY (wikiusers_id, threads_id)
);

CREATE TABLE revision_histories
(
    threads_id INTEGER NOT NULL,
    articles_id INTEGER NOT NULL,
    -- A Unix time value.
    revision_date INTEGER NOT NULL,
    wikiusers_id INTEGER NOT NULL,
    user_comment TEXT NOT NULL,
    FOREIGN KEY (threads_id)
        REFERENCES threads(id),
    FOREIGN KEY (wikiusers_id)
        REFERENCES wikiusers(id),
    FOREIGN KEY (articles_id)
        REFERENCES articles(id),
    PRIMARY KEY (threads_id, articles_id, revision_date, wikiusers_id)
);

-- Represents a link between one article and another.
CREATE TABLE links
(
    from_revision_histories_id INTEGER NOT NULL,
    to_title TEXT NOT NULL,
    FOREIGN KEY (from_revision_histories_id)
        REFERENCES revision_histories(id),
    PRIMARY KEY (from_revision_histories_id, to_title)
);

-- The "Admin" user (who owns various automatic edits) has user ID 1.
INSERT INTO wikiusers
    (username, password, email)
    VALUES
    ('Admin', NULL, NULL)
;

