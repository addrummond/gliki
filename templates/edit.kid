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
    <div class="edit_error">
        <p py:if="locals().has_key('error_message') and error_message">
            <b class="error">The change was not committed due to the following error:</b>
        </p>
        <p py:if="locals().has_key('error_message') and error_message" class="error">
            At line ${line}, column ${column}: ${error_message}
        </p>
        <p>
            If you are using a reasonably modern browser
            and have Javacript turned on,
            the cursor in the text box below will have been
            moved to the position of the error.
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

        <label class="f-title" id="____title_label" for="____title">Title</label>
        <input class="f-title" id="____title" type="text" name="new_title" value="${article_title}" size="70"></input>
        <br />
        <label class="f-comment" id="____comment_label" for="____comment">Comment</label>
        <input class="f-comment" id="____comment" type="text" name="comment" value="${comment}" size="70"></input>
        <br />
        <label for="____t1">Enter your text here:</label>
        <textarea name="sourceText" id="____t1" style="width: 100%;" name="source" cols="80" rows="25">${article_source}</textarea>
        <input name="update" type="submit" value="Update page"></input>
        <input name="preview" type="submit" value="Preview changes"></input>
    </form>
    <license_boilerplate />

    <script type="text/javascript">
    <!--
    function lineColToIndex(str, line, col) {
        // First get the index of the beginning of the line.
        var i;
        for (i = 0; i < str.length && line > 0; ++i) {
            if (str[i] == '\n') {
                --line;
            }
            else if (str[i] == '\r') {
                --line;
                ++i; // Presumably '\n' will follow.
            }
        }

        return i + col;
    }

    function setCursorPos(textArea, index) {
        if (textArea.selectionStart) { // Mozilla
            textArea.selectionStart = index;
        }
        else if (false) { // IE.
            // TODO.
        }
    }

    setCursorPos(document.sourceText, lineColToIndex(document.sourceText.value, ${line}, ${column}));
    -->
    </script>
</body>

</html>

