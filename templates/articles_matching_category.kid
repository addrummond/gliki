<?python
import urllib
import my_utils
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Category ${category}</title>
</head>

<body>
    <p>You can also look at a list of <a class="category_ref" href="${links.category_list_link()}">all the categories</a> in Gliki.</p>

    <p py:if="article_titles != []">The following articles are in category &lsquo;${category}&rsquo;:</p>

    <ol py:if="article_titles != []" class="article-list">
        <li py:for="title in article_titles"><a href="${links.article_link(title)}" class="article_ref">${title}</a></li>
    </ol>

    <p py:if="article_titles == []">
        There are currently no articles in category &lsquo;${category}&rsquo;.
    </p>
</body>
</html>

