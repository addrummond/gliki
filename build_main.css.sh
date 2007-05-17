#Process main.css.m4 removing all blank lines and comments after processing
(m4 main.css.m4) | (grep -v "^$\|^#\|^/\*#") > static/main.css

