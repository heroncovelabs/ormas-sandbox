"""Frozen observation runtime for hard_oss_v1 candidate-side probes (protocol observe-v1).

A probe runs inside the candidate checkout, in the candidate's interpreter, so
nothing it concludes can be trusted: candidate code can patch anything that runs
there. It therefore concludes nothing. It executes small behaviors and reports
what happened (values, exception types, sequences) as one JSON record. Every
assertion runs in the acceptance driver, in a separate process that holds no
candidate code.

Invocation: ``python3 -I oss_checks/<probe file> <probe name> <nonce>``. The
driver draws a fresh random nonce for every call. Output records are lines
``ORMAS-OBS <nonce> <kind> <json>`` written to a private duplicate of stdout:

- ``begin``: the probe started (before any candidate code is imported);
- ``setup``: the package could not be imported (or came from the wrong place);
- ``ready``: setup finished, the probe starts;
- ``result``: the observations. If the probe was interrupted by any exception,
  including ``SystemExit``, ``KeyboardInterrupt`` or a test framework's skip, the
  record is ``{"__raised__": ...}``.

The process then ends with ``os._exit`` so no candidate exit handler runs after
the record. The driver accepts exactly ``begin``, ``ready``, ``result`` with its
nonce. ``begin`` without ``setup`` or ``ready`` means the candidate ended the
process while it was being imported.
"""
from __future__ import annotations

import json
import os
import sys

_TAG = "ORMAS-OBS"
_dumps = json.dumps
_write = os.write
_exit = os._exit
_PLAIN = (str, int, float, bool, type(None))


def value(obj, depth=0):
    """A JSON-safe description of ``obj`` using exact builtin types only.

    Subclasses and other objects are described by type name, so a candidate
    object can never stand in for a plain value in the driver's comparison.
    """
    kind = type(obj)
    if kind in _PLAIN:
        return obj
    if depth < 8 and kind in (list, tuple):
        return [value(item, depth + 1) for item in obj]
    if depth < 8 and kind is dict and all(type(k) is str for k in obj):
        return {k: value(v, depth + 1) for k, v in obj.items()}
    if kind is bytes:
        return {"bytes": obj.decode("latin-1")}
    return {"object": kind.__name__}


def exc(error, watch=None):
    """Describe an exception: its type name and which watched classes it is an instance of."""
    try:
        message = str(error)[:500]
    except BaseException:  # noqa: BLE001
        message = "<str() failed>"
    out = {"raised": type(error).__name__, "message": message}
    if watch:
        out["isa"] = sorted(name for name, cls in watch.items() if isinstance(cls, type) and isinstance(error, cls))
    return out


def attempt(fn, watch=None):
    """``{"ok": value(fn())}``, or the exception's description if ``fn`` raised anything."""
    try:
        return {"ok": value(fn())}
    except BaseException as error:  # noqa: BLE001
        return exc(error, watch)


def main(setup, probes):
    """Run one probe named on the command line; never returns."""
    if len(sys.argv) != 3:
        sys.stderr.write("usage: probe <name> <nonce>\n")
        _exit(2)
    name, nonce = sys.argv[1], sys.argv[2]
    del sys.argv[1:]
    out = os.dup(1)

    def emit(kind, payload):
        line = "%s %s %s %s\n" % (_TAG, nonce, kind, _dumps(payload, sort_keys=True, ensure_ascii=True))
        data = line.encode("ascii")
        while data:
            data = data[_write(out, data):]

    emit("begin", {})
    if name not in probes:
        emit("setup", {"error": "unknown probe %r" % name})
        _exit(2)
    try:
        setup()
    except BaseException as error:  # noqa: BLE001
        emit("setup", exc(error))
        _exit(3)
    emit("ready", {})
    try:
        observations = value(probes[name]())
    except BaseException as error:  # noqa: BLE001
        observations = {"__raised__": exc(error)}
    emit("result", observations)
    _exit(0)
