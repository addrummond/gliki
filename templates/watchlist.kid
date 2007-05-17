<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${username} - Watchlist</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}
    </p>

    <p py:if="not locals().has_key('error') and len(article_titles) == 0">
        Currently, you do not have any articles on your watchlist.
    </p>

    <p py:if="not locals().has_key('error') and len(article_titles) > 0">
        You can look at the list of
        <a href="${links.tracked_changes_link()}">articles on your watchlist which have recently changed</a>.
    </p>
    <p py:if="not locals().has_key('error') and len(article_titles) > 0">
        The following articles are on your watchlist:
    </p>

    <ol py:if="not locals().has_key('error') and len(article_titles) > 0" class="article-list">
        <li py:for="title in article_titles"><a href="${links.article_link(title)}" class="article_ref">${title}</a></li>
    </ol>
</body>
</html>

