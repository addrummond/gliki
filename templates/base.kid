<?python
import urllib
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <title py:match="item.tag=='{http://www.w3.org/1999/xhtml}title'" py:attrs="item.items()">
        <span py:replace="[item.text] + item[:]">The title</span>
        ${(not item.text.startswith('Gliki')) and '- Gliki' or ''}
    </title>
    <span py:replace="[x for x in item[:] if x.tag != '{http://www.w3.org/1999/xhtml}title}']"></span>
    <link href="/main.css" rel="stylesheet" type="text/css" />
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <p style="color: darkred;">
        <b><i>To all intrepid travelers of the interweb: This is currently just up
              for testing purposes. Feel free to mess around with it, but don't expect
              it to work or anything.</i></b>
    </p>
    <img class="logo" src="/logo.png" alt="Gliki - the generative linguistics wiki"/>
    <p class="login-message" py:if="(locals().has_key('username') or globals().has_key('username')) and username">
        <i>You are logged in as <a class="article_ref" href="${links.user_page_link(username)}">${username}</a></i>
    </p>
    <p class="login-message" py:if="(not locals().has_key('username')) or (not username)">
        <i>You are not currently logged in.</i>
        <a class="action" href="${links.create_account_link()}">create an account</a> |
        <a class="action" href="${links.login_link()}">log in</a>.
    </p>
    <ul class="home"><li><a class="button" href="/">Home</a></li></ul>
    <span py:replace="item[:]">The body.</span>
</body>

</html>

