<?python
import urllib
import my_utils
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
        <a class="article_ref" href="/articles/${my_utils.futz_article_title(urllib.quote(article_title))}">${article_title}</a>
        has been added to your <a href="/watchlist">watchlist</a>.
    </p>
</body>
</html>

