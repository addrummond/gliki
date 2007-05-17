<?python import urllib ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Delete account</title>
</head>

<body>
    <p py:if="locals().has_key('error')">
        ${error}.
    </p>
    <p py:if="locals().has_key('username_')">
        The account &lsquo;${username_}&rsquo; has been deleted. All edits
        made by this user are still present and recorded in article histories.
        The userpage for this user has been deleted.
    </p>
</body>
</html>

