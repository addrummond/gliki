<?python
import urllib
import links
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid', 'license_boilerplate.kid'">
<head>
    <title>Gliki - The generative linguistics wiki</title>
</head>

<body>
    <h1>Welcome to Gliki</h1>

    <p>
    Gliki is a wiki for generative linguistics.
    The idea is for people to write articles collaberatively on topics which interest them.
    You can write in whatever style you like, and on whatever topic.
    Even topics outside linguistics altogether are OK, but
    but the site has various features designed for linguists.
    Currently, these mostly favor syntacticians:
    numbered and glossed examples are supported,
    and there is a utility for rendering labelled bracketings
    as trees.
    </p>
    <p>
    You can start editing any page in the Wiki (except this one) right now,
    but you might want to <a class="action" href="${links.create_account_link()}">create an account</a> first,
    or <a class="action" href="${links.login_link()}">log in</a> if you already have an account.
    </p>
    <p>
    <b>For more detailed information about the site,
    see the <a href="${links.article_link('Gliki')}" class="article_ref">Gliki</a> article and
    the list of <a href="${links.article_link('Useful-links')}" class="article_ref">useful links</a>.</b>
    </p>
    <p>
    If you're new to wikis in general, you might want to read the
    <a href="http://en.wikipedia.org/wiki/Wiki" class="external_link">Wikipedia article on wikis</a>.
    </p>
    <license_boilerplate />
    <p>
    Gliki uses custom software which is currently in the early stages of development,
    so there are a few missing features, and probably some bugs.
    If something needs fixing, email <a href="mailto:webmaster@gliki.whsites.net" class="external_link">webmaster@gliki.whsites.net</a>.
    </p>
    <p>
    For those who care about such things, Gliki is written in
    <a href="http://www.python.org" class="external_link">Python</a>,
    using
    <a href="http://www.sqlite.org" class="external_link">SQLite</a> for the database.
    </p>
</body>
</html>

