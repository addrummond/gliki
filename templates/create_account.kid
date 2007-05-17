<?python
import urllib
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Create a Gliki account</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        <b class="error">${error}</b>
    </p>
    <form method="POST" action="${links.make_new_account_link()}">
        <table>
            <tr>
                <th>Email</th>
                <td><input type="text" name="email" value="${locals().has_key('default_email') and default_email or ''}"></input></td>
                <td>(optional)</td>
            </tr>
            <tr>
                <th>Username</th>
                <td><input type="text" name="username" value="${locals().has_key('default_username') and default_username or ''}"></input></td>
            </tr>
            <tr>
                <th>Password</th>
                <td><input type="password" name="password" value=""></input></td>
            </tr>
            <tr>
                <td><input type="submit" value="Create"></input></td>
            </tr>
        </table>
    </form>
</body>
</html>

