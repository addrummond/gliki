<?python
import urllib
import my_utils
import itertools
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${article_title} - Diff</title>
</head>

<body>
    <p>
        The difference between
        <a class="article_ref" href="${links.article_link(article_title)}">${article_title}</a>
        revision ${rev1} and revision ${rev2} is as follows.
    </p>
    <p py:if="newtitle">
        The title of revision ${rev1} is &lsquo;${oldtitle}&rsquo;; the title of revision ${rev2} is &lsquo;${newtitle}&rsquo;.
    </p>
    <p py:if="formertitle">
        Note: At the time, this article was called &lsquo;${formertitle}&rsquo;.
    </p>
    <p py:if="not (diff_html or newtitle)">
        There is no difference between revision ${rev1} and revision ${rev2} of
        <a class="article_ref" href="${links.article_link(article_title)}">${article_title}</a>.
    </p>
    <p py:if="revision_comment">
        <b>Comment:</b>
        ${revision_comment}.
    </p>
    <hr />
    <p>
        You might want to read about
        <a href="${links.article_link('Gliki-revision-numbering')}" class="article_ref">
        Gliki's revision numbering system.
        </a>
    </p>
${diff_html and XML(diff_html) or ''}
</body>
</html>

