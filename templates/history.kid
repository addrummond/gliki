<?python
import urllib
import my_utils
import itertools
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${article_title} - History</title>
</head>

<body>
    <p>History for <a href="${links.article_link(article_title)}" class="article_ref"><b>${article_title}</b></a>:</p>
    <table class="history">
        <tr>
            <th>Date</th>
            <th>User</th>
            <th>Article title</th>
            <th>Comment</th>
        </tr>
        <tr py:for="r in revisions">
            <td>
                <table class="date-diff-pair">
                    <tr>
                        <td>
                            <a class="article_ref"
                               href="${links.article_link(article_title, r['diff_revs_pair'][0])}">
                                ${my_utils.standard_date_format(r['revision_date'])}
                            </a>
                        </td>
                       <td py:if="r['diff_revs_pair'][0] and r['diff_revs_pair'][1]">
                            <a class="diff_ref" href="${links.diff_link(article_title, r['diff_revs_pair'][0], r['diff_revs_pair'][1])}">
                diff w/previous
                            </a>
                       </td>
                    </tr>
                </table>
            </td>
            <td><a href="${links.user_page_link(r['username'])}" class="article_ref">${r['username']}</a></td>
            <td>${r['article_title']}</td>
            <td>${my_utils.truncate(200, r['comment'])}</td>
        </tr>
    </table>
</body>
</html>

