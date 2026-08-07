SDK Changelog
=============

All notable changes to the client SDK are recorded here. The project
follows **semantic versioning**: breaking changes bump the major number,
and any deprecation ships at least one minor release before removal.

3.0.0
-----

This is a *breaking* release. Review the removals before upgrading.

- **Added:** async iterators for every list endpoint, so pagination is
  transparent.
- **Changed:** ``Client.new`` now takes an options struct instead of
  positional arguments.
- **Removed:** the long-deprecated ``legacy_auth`` helper.

.. _section-1:

2.4.0
-----

- **Added:** automatic retry with exponential backoff on ``503``
  responses.
- **Fixed:** ``Timeout`` was ignored when a custom transport was
  supplied.

.. _section-2:

2.3.1
-----

- **Fixed:** a rare panic when the server returned an empty
  ``Content-Type``.

Deprecation Schedule
--------------------

Symbols slated for removal and their replacements:

=============== ============= ========== ===================
Symbol          Deprecated in Removed in Replacement
=============== ============= ========== ===================
``legacy_auth`` ``2.1.0``     ``3.0.0``  ``Client.with_key``
``sync_fetch``  ``2.4.0``     ``4.0.0``  ``fetch().await``
``RawResponse`` ``2.4.0``     ``4.0.0``  ``TypedResponse``
=============== ============= ========== ===================

Upgrade Notes
-------------

To move from 2.x to 3.0:

1. Replace positional ``Client.new`` calls with the options struct.
2. Swap any ``legacy_auth`` usage for ``Client.with_key``.
3. Run your test suite — the compiler flags most breakages, but
   *runtime* auth changes need a live check.
