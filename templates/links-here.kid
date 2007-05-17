<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${article_title} - What links here?</title>
</head>

<body>
    <div py:if="len(titles) == 0">
        Currently, no articles link to <a class="article_ref" href="${links.article_link(article_title)}">${article_title}</a>.
    </div>
    <div py:if="len(titles) > 0">
        The following articles link to <a class="article_ref" href="${links.article_link(article_title)}">${article_title}</a>.

        <ul class="links-here">
            <li py:for="t in titles">
                <a class="article_ref" href="${links.article_link(t)}">${t}</a>
            </li>
        </ul>
    </div>
</body>
</html>

