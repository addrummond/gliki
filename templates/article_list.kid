<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>List of all articles</title>
</head>

<body>
    <p>Articles from ${starting_from} to ${going_to} in alphabetical order:</p>

    <ol class="article-list">
        <li py:for="title in article_titles"><a href="${links.article_link(title)}" class="article_ref">${title}</a></li>
    </ol>
</body>
</html>

