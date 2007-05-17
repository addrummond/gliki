<?python
#import urllib
#import my_utils
#import itertools
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'base.kid'">
<head>
    <title>Syntax tree</title>
</head>

<body>
    <p>
        This is a utility for drawing syntax trees given a labelled
        bracketing. It can draw trees with bar levels and movement indicated
        by arrows (although the arrow drawing algorithm doesn't always work well
        at the moment). Here's a simple example:
    </p>
    <pre>
[S [NP [D the] [N cat]] [VP [V sat] [PP [P on] [NP [D the] [N mat]]]]]
    </pre>
    <p>
        It is possible to represent movements, which will be rendered with the
        appropriate arrows. Here's an example with a passive transformation:
    </p>
    <pre>
[S [-&gt;label NP [D the] [N man]] [Aux was] [VP [VP [V bitten] &lt;-label] [PP [P by] [NP [D the] [N dog]]]]]
    </pre>
    <p>
        The surface position of the moved constituent is labelled using the
        syntax &lsquo;-&gt;label&rsquo;, and its initial position is given
        a matching label using the syntax &lsquo;&lt;-label&rsquo;.
    </p>
    <form method="POST" action="/render-syntax-tree">
        <textarea name="tree" cols="100" rows="25"></textarea>
        <br />
        <input type="submit" value="Send"></input>
    </form>
</body>
</html>

