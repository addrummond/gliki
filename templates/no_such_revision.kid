<?python
import urllib
import my_utils
import itertools
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${article_title} - No such revision</title>
</head>

<body>
    <p py:if="kind == 'diff'">
        One of the revisions specified for this diff does not exist. Probably,
        you tried to diff the first revision of an article with its previous
        revision.
    </p>
    <p py:if="kind == 'show'">
        No such revision for this article.
    </p>
</body>
</html>

