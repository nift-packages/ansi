# ansi

Dependency-free ANSI Select Graphic Rendition (SGR) formatting for Nift 4.6.0
or newer. The package exports exactly one facade, `ansi`.

```nift
@import("ansi")

print(ansi.bold("important"))
print(ansi.red("error"))
print(ansi.wrap("custom", [1, 34]))
```

## API

- `ansi.sgr(codes)` returns an SGR sequence. `codes` is one integer or a
  non-empty array of integers.
- `ansi.wrap(text, codes)` surrounds text with the requested SGR sequence and
  `ansi.reset()`.
- `ansi.reset()` returns SGR reset (`0`).
- `ansi.bold(text)`, `ansi.dim(text)`, `ansi.italic(text)` and
  `ansi.underline(text)` wrap text with codes `1`, `2`, `3` and `4`.
- `ansi.black(text)`, `ansi.red(text)`, `ansi.green(text)`,
  `ansi.yellow(text)`, `ansi.blue(text)`, `ansi.magenta(text)`,
  `ansi.cyan(text)` and `ansi.white(text)` wrap text with foreground codes
  `30` through `37`.

Every code must be in `0..255`. `wrap` also requires string text, and style and
color helpers require string text. Invalid values return `null` and emit
nothing. Missing or extra arguments are rejected by Nift's arity checks.

The facade is intentionally deterministic and terminal-agnostic. Every valid
call returns ANSI bytes regardless of TTY detection, environment variables, or
color-support conventions. Empty text is still wrapped, repeated calls return
identical bytes, and existing escape sequences in text are neither parsed nor
removed. Consumers decide whether and where to output the returned string.

## Test

```sh
python3 -B tests/run.py /home/nick/Repositories/nift/nift/nift
```

The runner checks direct source import, installation with `nift add` into a
fresh temporary consumer, all facade operations, malformed and boundary input,
repeatability, and module/private-method isolation. Its temporary consumer is
created below `tests/` and removed on success or failure.
