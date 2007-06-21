# Copyright (C) 2007 Alex Drummond <a.d.drummond@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

#
# Gliki CSS Styling - James "Mue" Adams, 2006.
#

define(`BODY_BACKGROUND', `white')
define(`HEADING_COLOR', `#222')

define(`TEXT_COLOR', `black')

define(`OLD_TEXT_COLOR', `#ff9799')
define(`NEW_TEXT_COLOR', `#97ff99')

define(`TEXT_BASE_MIN', 10)
define(`TEXT_BASE_INC', 2)
define(`TEXT_BASE_UNITS', pt)
define(`TEXT_BASE', `eval(TEXT_BASE_MIN`+('$1`)*'TEXT_BASE_INC)'TEXT_BASE_UNITS)
define(`SMALL_TEXT', `8pt')

define(`TABLE_COLOR', `black')
define(`TABLE_HISTORY_COLOR', `black')

define(`LINK_BACKGROUND_COLOR', `#e7efff')
define(`HIGHLIGHTED_LINK_BACKGROUND_COLOR', `#DDE')

define(`PRE_COLOR', `black')

define(`LINE_HEIGHT', `18pt')

define(`SECTION_INDENT', `eval(`('$1`-1)*10')pt')

define(`LIGHT_BORDER_COLOR', `#BBB')

define(`EXTERNAL_LINK_COLOR', `#04681e')
define(`INTERNAL_LINK_COLOR', `#3939ff')
define(`EXAMPLE_LINK_COLOR', `#3939ff')
define(`CATEGORY_REF_COLOR', `#ff7e00')

define(`PREVIEW_BACKGROUND_COLOR', `#feffb2')

define(`UNDERLINE_GREY', `#AAA')

define(`PRE_BACKGROUND_COLOR', `#fcfdcc')

define(`BUTTON_SEP', `1.5em')

define(`INDENT_DISTANCE', `2em')

define(`LMESSAGE_TOP_PADDING', `1em')

define(`SEARCH_BOX_BACKGROUND', BODY_BACKGROUND)

body {
  margin-top: 2px;
  padding-top: 0;
  font-family: verdana, arial, helvetica, sans-serif;
  font-size: TEXT_BASE(0);
  line-height: LINE_HEIGHT;
  background-color: BODY_BACKGROUND;
}

h1 {
  font-size: TEXT_BASE(3);
  color: HEADING_COLOR;
}

h2 {
  font-size: TEXT_BASE(2);
  color: HEADING_COLOR;
  position: relative;
  left: SECTION_INDENT(1);
}

h3 {
  font-size: TEXT_BASE(1);
  color: HEADING_COLOR;
  position: relative;
  left: SECTION_INDENT(2);
}

h4 {
  font-size: TEXT_BASE(0);
  font-weight: bold;
  text-decoration: underline;
  color: HEADING_COLOR;
  position: relative;
  left: SECTION_INDENT(3);
}

h5 {
  font-size: TEXT_BASE(0);
  font-weight: normal;
  font-style: italic;
  color: HEADING_COLOR;
  position: relative;
  left: SECTION_INDENT(4);
}

p {
  font-size: TEXT_BASE(0);
  color: TEXT_COLOR;
}

ul {
  list-style-type: square;
}

ol.article-list {
  list-style-type: decimal;
}

define(`ACTIONS_CSS',
`  list-style: none;
    margin-top: 0;
    padding-top: 0;
    padding-left: 0;
    margin-left: 0;
    clear: left;')

ul.home {
  ACTIONS_CSS
  padding-bottom: BUTTON_SEP;
}

ul.home li {
  float: left;
  margin-right: 1em;
}

ul.user-actions {
  ACTIONS_CSS
  padding-bottom: BUTTON_SEP;
}

ul.user-actions li {
  float:left;
  margin-right: 1em;
}

ul.article-actions {
  ACTIONS_CSS
}

ul.article-actions li {
  float: left;
  margin-right: 1em;
}

h1.article-title {
  clear:both;
  margin-top: 0;
  padding-top: 0.5em;
}

div.article-text {
  clear: both;
  position: relative;
  margin: 0;
  padding: 0;
}

div.comment {
  width: 100%;
# color: TABLE_COLOR;
  border-bottom: 1px dashed LIGHT_BORDER_COLOR;
}

p.comment-header {
  margin-bottom: 0.2em;
}
p.comment-header + p {
  margin-top: 0.2em;
}

form.create-account th {
  text-align: left;
}

th { padding-right: 1em; }

table {
  font-size: 1em;
  color: TABLE_COLOR;
}

table.history {
  font-size: 1em;
  color: TABLE_HISTORY_COLOR;
  border-top: 1px solid LIGHT_BORDER_COLOR;
  border-bottom: 1px solid LIGHT_BORDER_COLOR;
  padding: 0;
  margin: 0;
  border-collapse: collapse;
}

table.history tr {
  padding: 0;
  margin: 0;
}

table.history th {
  text-align: left;
  border-bottom: 1px solid LIGHT_BORDER_COLOR;
  padding: 0.5em;
  margin: 0;
}

table.history td {
  border-bottom: 1px dotted LIGHT_BORDER_COLOR;
  padding: 0.2em 0.5em 0.2em 0.5em;
  margin: 0;
}

table.date-diff-pair td {
    border: none;
    padding-left: 0;
    padding-right: 0;
    padding-top: 0;
    padding-bottom: 0;
}

table.date-diff-pair td + td {
  padding-left: 1.0em;
}

form.comment-form table th { 
  text-align: left;
}

a {
  color: black;
  font-size: TEXT_BASE(0);
  text-decoration: none;
  padding-left: 0.2em;
  padding-right: 0.2em;
  padding-top: 0.1em;
  padding-bottom: 0.1em;
  margin: 0;
  line-height: 25px;
  border-bottom: 1px dashed UNDERLINE_GREY;
}

a.action {
  font-weight: bold;
}

a.button {
  border: 1px dashed UNDERLINE_GREY;
}

a.footnote-link {
  border: none;
  padding: 0 0;
}
a.footnote-link:hover {
  border: none;
}

a.external_link {
  color: EXTERNAL_LINK_COLOR;
}

a.article_ref {
  color: INTERNAL_LINK_COLOR;
}

a.category_ref {
  color: CATEGORY_REF_COLOR;
}

a.non-existent {
  color: red;
}

a.revision_ref {
  color: INTERNAL_LINK_COLOR;
}

a.diff_ref {
  color: INTERNAL_LINK_COLOR;
}

a.example_ref {
  color: EXAMPLE_LINK_COLOR;
  border: none;
}
a.example_ref:hover {
  border: none;
}

a.button:link {
  background-color: LINK_BACKGROUND_COLOR;
}

a.button:visited {
  background-color: LINK_BACKGROUND_COLOR; /* Was HIGHLIGHTED_* */
}

a.button:active {
  background-color: LINK_BACKGROUND_COLOR; /* Was HIGHLIGHTED_* */
}

a:hover {
  border-bottom-style: solid;
}
a.button:hover {
  border-style: solid;
}

img {
  border: none;
}

pre {
  background-color: PRE_BACKGROUND_COLOR;
  color: PRE_COLOR;
  text-decoration: none;
  border: 1px dashed UNDERLINE_GREY;
  padding-left: 0.2em;
  padding-right: 0.2em;
  padding-top: 0.1em;
  padding-bottom: 0.1em;
  margin: 0;
  line-height: 25px;
  font-size: 9pt;
}

td.old-text {
  padding: 0.25em;
  background-color: OLD_TEXT_COLOR;
}

td.new-text {
  padding:0.25em;
  background-color: NEW_TEXT_COLOR;
}

td.new-text-plus {
  font-size: 20pt;
  padding-left: 1em;
}

td.old-text-minus {
  font-size: 20pt;
}

.error { padding: 0.25em; background-color: OLD_TEXT_COLOR; }

.preview_background { background-color: PREVIEW_BACKGROUND_COLOR; }

table.preferences th { text-align: left; }

p.categories {
  float: left;
  clear: left;
  font-size: SMALL_TEXT; 
  margin-top: 0;
  padding-top: 0.25em;
}
p.categories a {
  font-size: SMALL_TEXT;
}
p.categories span a {
  font-size: SMALL_TEXT;
}
span.category-sep {
  color: UNDERLINE_GREY;
}

p.redirects {
  font-size: SMALL_TEXT;
  font-style: italic;
  padding-top: 0;
  margin-top: 0;
  padding-bottom: 0;
  margin-bottom: 0;
}

form.edit th { text-align: left; }

img.logo { clear: both; }

form label { font-weight: bold; }
form input.f-title {
  position: absolute;
  left: 8em;
}
form input.f-comment {
  position: absolute;
  left: 8em;
}

p.login-message {
  font-size: SMALL_TEXT;
  clear: none;
  padding-top: LMESSAGE_TOP_PADDING;
  margin-top: 0;
}
p.login-message a {
  font-size: SMALL_TEXT;
}

div.left-indent {
  padding-left: INDENT_DISTANCE;
}
div.right-indent {
  padding-right: INDENT_DISTANCE;
}

td.explanation {
  font-style: italic;
  padding-left: 1em;
}

div.diff-box {
  margin-bottom: 2em;
}

p.error-loc {
  font-size: SMALL_TEXT;
}
p.error-loc a {
  font-size: SMALL_TEXT;
}

form.search-box {
  margin-top: LMESSAGE_TOP_PADDING;
  padding-top: LMESSAGE_TOP_PADDING;
  padding-left: 1em;
  padding-right: 1em;
  padding-bottom: 0;
  float: right;
  clear: none;
  background-color: SEARCH_BOX_BACKGROUND;
  border-color: LIGHT_BORDER_COLOR;
  border-style: dashed;
  border-width: 1px;
  text-align: right;
}
form.search-box button {
  border-style: none;
  background-color: BODY_BACKGROUND;
  font-size: SMALL_TEXT;
  font-weight: bold;
  padding-top: 0.5em;
  padding-right: 0;
  margin-right: 0;
  margin-bottom: 0;
  padding-bottom: 0.25em;
  text-align: right;
  cursor: pointer;
}

