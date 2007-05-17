<?python
import urllib
import my_utils
import links
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid', 'comment_form.kid'">

<head>
    <title>Error in comment on ${article_title}</title>
</head>

<body>
    <div py:if="locals().has_key('error_message') and error_message" py:strip="True">
        <p class="error">
            <b>Your comment on </b>
            <a class="article_ref" href="links.article_link(article_title)}">${article_title}</a>        
            <b>could not be posted due to the following error:</b>
        </p>
        <p class="error">
            At line ${line}, column ${column}: ${error_message}
        </p>
    </div>
    <div py:if="locals().has_key('preview') and preview" py:strip="True">
        <p>
            <b class="error">This is a preview of your comment. Changes have not yet been saved.</b>
        </p>
        <p>
            <a class="action" href="#____edit">&raquo; edit your changes</a>
        </p>
<div class="preview_background">
${XML(preview)}
</div>
    </div>

    <comment_form></comment_form>
</body>

</html>

