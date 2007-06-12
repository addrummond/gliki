<?python
import etc.customize as customize
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Blocked</title>
</head>

<body>
    <div py:strip="True" py:if="because == 'by_ip'">
        ${XML(customize.BLOCKED_BY_IP_MESSAGE_XHTML)}
    </div>
    <div py:strip="True" py:if="because == 'by_username'">
        ${XML(customize.BLOCKED_BY_USERNAME_MESSAGE_XHTML)}
    </div>
</body>
</html>

