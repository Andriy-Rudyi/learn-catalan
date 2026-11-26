"""Sections for learning the other languages of the site (LangWave).

The Catalan site keeps its own blueprints. Every other language in
``flaskblog.sites.SITES`` gets the same set of pages from this package,
filled from data files under ``langsites/data/<code>/``:

* ``/<site>/`` the section's start page;
* ``/<site>/dictionary`` search, in the language learnt or in a translation;
* ``/<site>/dictionary/<word>`` a word with its meanings and translations.

A section is shown only while its site is ``enabled``; until then only the
site's editor (``flaskblog.permissions.is_admin``) can open it, so it can be
built and checked on the live site without anybody else seeing it.

The addresses are paths (``/ukrainian/...``) for now. Once BASE_DOMAIN is
set, each section will move to its own subdomain (``ukrainian.<domain>``),
like the Catalan site.
"""
