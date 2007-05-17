<?python
import urllib
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Confirm deletion of your account</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}
    </p>
    <p py:if="locals().has_key('username')">Are you sure you want to delete your user account &lsquo;${username}&rsquo;?</p>
    <form py:if="locals().has_key('username')" method="POST" action="${links.delete_account_link()}">
        <input type="submit" value="Yes, delete it"></input>
    </form>
</body>
</html>

