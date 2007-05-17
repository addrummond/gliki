<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>List of all categories</title>
</head>

<body>
    <p>Gliki currently has the following categories:</p>

    <ol class="article-list">
        <li py:for="cat in categories"><a class="category_ref" href="${links.category_link(cat)}">${cat}</a></li>
    </ol>
</body>
</html>

