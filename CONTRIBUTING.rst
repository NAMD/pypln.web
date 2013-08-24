Contributing
============

Contact Information
-------------------

You can interact with us through:

- Mailling list: `pypln @ Google Groups <https://groups.google.com/group/pypln>`_
- IRC: `#pypln @ irc.freenode.net <http://webchat.freenode.net?channels=pypln>`_


Code Guidelines
---------------

- **Please**, use `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_.
- Write tests for every feature you add or bug you solve (preferably use
  `test-driven development <https://en.wikipedia.org/wiki/Test-driven_development>`_).
- `Commented code is dead code <http://www.codinghorror.com/blog/2008/07/coding-without-comments.html>`_.
- Name identifiers (variable, class, function, module names) with readable
  names (``x`` is always wrong).
- Use `Python's new-style formatting <http://docs.python.org/library/string.html#format-string-syntax>`_
  (``'{} = {}'.format(a, b)`` instead of ``'%s = %s' % (a, b)``).
- All ``#TODO`` should be turned into issues (use
  `GitHub issue system <https://github.com/namd/pypln.web/issues>`_).
- Run all tests before pushing (just execute ``make test``).
- Try to write Python3-friendly code, so when we decide to support both Python2
  and Python3, it'll not be a pain.


Git Usage
---------

- We use `git flow <https://github.com/nvie/gitflow>`_, so you must (learn more
  about this `successul Git branching model <http://nvie.com/posts/a-successful-git-branching-model/>`_).
- Please `write decent commit messages <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.
