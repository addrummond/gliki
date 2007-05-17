<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${locals().has_key('username') and username + ' - ' or ''}Watchlist</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}
    </p>
    <p py:if="not locals().has_key('error')">
        <a href="${links.article_link(article_title)}">${article_title}</a>
        has been removed from your <a href="${links.watchlist_link()}">watchlist</a>.
    </p>
</body>
</html>

