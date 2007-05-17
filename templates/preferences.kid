<?python
import urllib
import my_utils
import itertools
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>${locals().has_key('username') and username + ' - ' or ''}Preferences</title>
</head>

<body>
    <p py:if="not found">
        No preferences could be found.
        This is probably because you are not
        <a class="action" href="${links.login_link()}">logged in</a>.
    </p>
    <p py:if="found and not updated">
        The following preferences are currently set for user ${username}:
    </p>
    <p py:if="found and updated">
        <b>Your preferences have been updated:</b>
    </p>
    <form py:if="found" method="POST" action="${links.update_preferences_link()}">
        <input type="hidden" name="username" value="${username}"></input>
        <table class="preferences">
            <tr>
                <th>Send watchlist updates by email</th>
                <td>
                    <input type="checkbox" name="email_changes" py:attrs="(email_changes and (dict(checked=''),) or ({ },))[0]"></input>
                </td>
            </tr>
            <tr>
                <th>Send updates in a daily digest</th>
                <td>
                    <input type="checkbox" name="digest" py:attrs="(digest and (dict(checked=''),) or ({ },))[0]"></input>
                </td>
            </tr>
            <tr>
                <td><input type="submit" value="Change my preferences"></input></td>
            </tr>
        </table>
    </form>
</body>
</html>

