<?python
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
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import urllib
import my_utils
import links
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="base.kid, license_boilerplate.kid">
<head>
  <title>Editing - ${article_title}</title>
</head>

<body>
    <div class="edit_error" py:if="locals().has_key('error_message') and error_message">
        <p> 
            <b class="error">The change was not committed due to the following error:</b>
        </p>
        <p class="error">
            At line ${line}, column ${column}: ${error_message}
        </p>
        <p>
            If you are using a reasonably modern browser
            and have Javacript turned on,
            the region in the text box near the error
            will have been highlighted.
        </p>
    </div>

    <div py:if="locals().has_key('preview') and preview" py:strip="True">
        <p>
            <b class="error">This is a preview. Changes have not yet been saved.</b>
        </p>
        <p>
            <a class="action" href="#____edit">&raquo; edit your changes</a>
        </p>
<div class="preview_background">
${XML(preview)}
</div>
    <hr />
    </div>

    <form style="width:100%;" class="edit" id="____edit" method="POST"
          py:attrs="dict(action = (locals().has_key('threads_id') and threads_id) and links.revise_link_by_threads_id(threads_id) or links.revise_link_by_title(article_title))">
        <input py:if="locals().has_key('threads_id') and threads_id and locals().has_key('article_title') and article_title"
               type="hidden" name="redundant_title" value="${article_title}"></input>
        <input type="hidden" name="edit_time" value="${edit_time}"></input>

        <label class="f-title" id="____title_label" for="____title">Title</label>
        <input class="f-title" id="____title" type="text" name="new_title" value="${article_title}" size="70"></input>
        <br />
        <label class="f-comment" id="____comment_label" for="____comment">Comment</label>
        <input class="f-comment" id="____comment" type="text" name="comment" value="${comment}" size="70"></input>
        <br />
        <label for="____t1">Enter your text here:</label>
        <textarea id="____t1" style="width: 100%;" name="source" cols="80" rows="25">${article_source}</textarea>
        <input name="update" type="submit" value="Update page"></input>
        <input name="preview" type="submit" value="Preview changes"></input>
    </form>
    <license_boilerplate />

    <form>
        <input type="hidden" id="____errorLineNumber" value="${locals().has_key('line') and line or 1}"></input>
        <input type="hidden" id="____errorColumnNumber" value="${locals().has_key('column') and column or 0}"></input>
    </form>
    <script type="text/javascript">
    <!--
    function lineColToIndex(str, line, col) {
        // First get the index of the beginning of the line.
        var i;
        for (i = 0; i < str.length && line > 1; ++i) {
            if (str[i] == '\n') {
                line -= 1;
            }
            else if (str[i] == '\r') {
                line -= 1;
                ++i; // Presumably '\n' will follow.
            }
        }

        return i + col;
    }

    function setCursorPos(textArea, index) {
        if (textArea.selectionStart) { // Mozilla
            textArea.selectionStart = index;
            textArea.selectionEnd = index == 0 ? index : index + 5;
        }
        else if (false) { // IE.
            // TODO.
        }
    }

    var text = document.getElementById('____t1')
    setCursorPos(
        text,
        lineColToIndex(
            text.value,
            parseInt(document.getElementById('____errorLineNumber').value),
            parseInt(document.getElementById('____errorColumnNumber').value)
        )
    );

    text.focus()
    -->
    </script>
</body>

</html>

