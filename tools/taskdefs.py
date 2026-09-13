"""Source-of-truth definitions for the thirty tasks (Builder A).

`tools/gen_tasks.py` turns each entry into a concrete task directory under
`tasks/` exactly as SPEC.md Sec 1 lays it out. Expected values are never written
by hand: the generator executes the reference and records what it returns, so a
spec that disagrees with its reference is a spec bug, not an expected-value bug.

Fields
    id            t<NN>_<slug>
    function      the function the agent must implement
    title         one line, shown as the spec heading
    category      string | list | date | number
    return_type   str | int | float | bool | list | dict   (the mutator uses it)
    signature     exact text after `def ` (shared by reference.py and the stub)
    doc           one-line docstring
    description   markdown behaviour rules shown to the agent
    imports       optional import lines for reference.py
    body          reference body (indented four spaces)
    visible       2-4 cases -> tests/test_visible.py; the first n_examples are the spec examples
    hidden        8-15 cases -> .grader/
    probes        8-12 FRESH cases; inputs appear in no other file of the task
"""

MEASURED = [
    "t03_roman_to_int",
    "t06_chunk_list",
    "t08_caesar_shift",
    "t10_median",
    "t11_normalize_whitespace",
    "t19_flatten",
    "t21_balanced_brackets",
    "t23_dedupe",
    "t24_transpose",
    "t25_hex_to_rgb",
]

SPARES = [
    "t01_slugify",
    "t09_vowel_counts",
    "t12_camel_to_snake",
    "t27_leap_years",
    "t28_running_average",
]

TO_MUTATE = [
    "t02_run_length_encode",
    "t04_day_of_week",
    "t05_parse_duration",
    "t07_merge_intervals",
    "t13_validate_isbn10",
    "t14_luhn_check_digit",
    "t15_group_anagrams",
    "t16_top_k_tokens",
    "t17_format_bytes",
    "t18_business_days",
    "t20_avg_word_length",
    "t22_word_wrap",
    "t26_semver_compare",
    "t29_extract_hashtags",
    "t30_char_frequency",
]

TASKS = []

TASKS.append({
    "id": "t01_slugify",
    "function": "slugify",
    "title": "Slugify a title",
    "category": "string",
    "return_type": "str",
    "signature": "slugify(text: str) -> str",
    "doc": "Turn a title into a lowercase hyphen-separated slug.",
    "description": """\
Turn `text` into a URL slug.

- Lowercase the whole string first.
- Keep ASCII letters `a`-`z` and ASCII digits `0`-`9` as they are.
- Replace every other character (including spaces, punctuation and any
  non-ASCII character) with a single hyphen `-`.
- Collapse any run of two or more consecutive hyphens into one hyphen.
- Strip hyphens from the start and the end of the result.
- If nothing is left, return the empty string `""`.""",
    "body": """\
    chars = []
    for ch in text.lower():
        if ch.isascii() and ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")""",
    "visible": [
        {"args": ["Hello, World!"], "kwargs": {}},
        {"args": ["  Python 3.12 Rocks  "], "kwargs": {}},
        {"args": ["---"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["Clean--Code"], "kwargs": {}},
        {"args": ["A"], "kwargs": {}},
        {"args": ["2026 Report: Q3"], "kwargs": {}},
        {"args": ["  leading and trailing  "], "kwargs": {}},
        {"args": ["___"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
        {"args": ["Rust&Go"], "kwargs": {}},
        {"args": ["CamelCase Title"], "kwargs": {}},
        {"args": ["a-b-c"], "kwargs": {}},
        {"args": ["99 Bottles of Beer!"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["Ice Cream & Cake"], "kwargs": {}},
        {"args": ["v1.2.3-beta"], "kwargs": {}},
        {"args": ["Zebra!!!Stripes"], "kwargs": {}},
        {"args": ["  spaced   out  "], "kwargs": {}},
        {"args": ["###"], "kwargs": {}},
        {"args": ["OneWord"], "kwargs": {}},
        {"args": ["7 Samurai"], "kwargs": {}},
        {"args": ["mixed_CASE_99"], "kwargs": {}},
        {"args": ["end-"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t02_run_length_encode",
    "function": "run_length_encode",
    "title": "Run-length encode a string",
    "category": "string",
    "return_type": "str",
    "signature": "run_length_encode(text: str) -> str",
    "doc": "Encode each run of repeated characters as the character followed by its count.",
    "description": """\
Encode `text` with run-length encoding.

- Walk the string left to right and split it into maximal runs of the same
  character.
- Emit each run as the character followed immediately by the run length written
  in decimal.
- Always write the count, including when it is `1`: `"abc"` becomes `"a1b1c1"`.
- The comparison is case-sensitive: `"aA"` becomes `"a1A1"`.
- Spaces and punctuation are ordinary characters and are encoded the same way.
- The empty string returns the empty string `""`.""",
    "body": """\
    if not text:
        return ""
    parts = []
    current = text[0]
    count = 1
    for ch in text[1:]:
        if ch == current:
            count += 1
        else:
            parts.append(current + str(count))
            current = ch
            count = 1
    parts.append(current + str(count))
    return "".join(parts)""",
    "visible": [
        {"args": ["aaabbc"], "kwargs": {}},
        {"args": ["abc"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["a"], "kwargs": {}},
        {"args": ["aaaa"], "kwargs": {}},
        {"args": ["wwwwwwwwwwww"], "kwargs": {}},
        {"args": ["abbccc"], "kwargs": {}},
        {"args": ["Mississippi"], "kwargs": {}},
        {"args": ["zzZZzz"], "kwargs": {}},
        {"args": ["  "], "kwargs": {}},
        {"args": ["112233"], "kwargs": {}},
        {"args": ["xyzzy"], "kwargs": {}},
        {"args": ["aabbaabb"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["qqqqq"], "kwargs": {}},
        {"args": ["Hello"], "kwargs": {}},
        {"args": ["ddddeeeefff"], "kwargs": {}},
        {"args": ["7777777777"], "kwargs": {}},
        {"args": ["kkkK"], "kwargs": {}},
        {"args": ["banana"], "kwargs": {}},
        {"args": ["pppqqq"], "kwargs": {}},
        {"args": ["AAAaaa"], "kwargs": {}},
        {"args": ["nnnnnnnnnn"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t03_roman_to_int",
    "function": "roman_to_int",
    "title": "Roman numeral to integer",
    "category": "string",
    "return_type": "int",
    "signature": "roman_to_int(roman: str) -> int",
    "doc": "Convert an uppercase Roman numeral to its integer value.",
    "description": """\
Convert the Roman numeral `roman` to an integer.

- The input is always a well-formed uppercase Roman numeral for a value from
  1 to 3999. You do not need to validate it.
- Letter values: `I` = 1, `V` = 5, `X` = 10, `L` = 50, `C` = 100, `D` = 500,
  `M` = 1000.
- A letter placed before a larger-valued letter is subtracted; the six
  subtractive pairs are `IV` = 4, `IX` = 9, `XL` = 40, `XC` = 90, `CD` = 400
  and `CM` = 900.
- Otherwise the letter values are added left to right.""",
    "body": """\
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for ch in reversed(roman):
        value = values[ch]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total""",
    "visible": [
        {"args": ["III"], "kwargs": {}},
        {"args": ["MCMXCIV"], "kwargs": {}},
        {"args": ["LVIII"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["I"], "kwargs": {}},
        {"args": ["IV"], "kwargs": {}},
        {"args": ["IX"], "kwargs": {}},
        {"args": ["XL"], "kwargs": {}},
        {"args": ["XC"], "kwargs": {}},
        {"args": ["CD"], "kwargs": {}},
        {"args": ["CM"], "kwargs": {}},
        {"args": ["MMXXVI"], "kwargs": {}},
        {"args": ["XLII"], "kwargs": {}},
        {"args": ["DCCCXC"], "kwargs": {}},
        {"args": ["MMMCMXCIX"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["VII"], "kwargs": {}},
        {"args": ["XIII"], "kwargs": {}},
        {"args": ["XXIX"], "kwargs": {}},
        {"args": ["LXXVI"], "kwargs": {}},
        {"args": ["CLXI"], "kwargs": {}},
        {"args": ["CDXLIV"], "kwargs": {}},
        {"args": ["MMCMLXXX"], "kwargs": {}},
        {"args": ["DXCV"], "kwargs": {}},
        {"args": ["MCMLXXXIV"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t04_day_of_week",
    "function": "day_of_week",
    "title": "ISO date to weekday name",
    "category": "date",
    "return_type": "str",
    "signature": "day_of_week(iso_date: str) -> str",
    "doc": "Return the English weekday name of an ISO-8601 calendar date.",
    "description": """\
Return the weekday of the date `iso_date`.

- `iso_date` is always a valid date in `YYYY-MM-DD` form (proleptic Gregorian
  calendar). You do not need to validate it.
- Return the English weekday name, capitalised, exactly one of: `"Monday"`,
  `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`,
  `"Sunday"`.
- Do not abbreviate and do not use the locale: the names above are literal.""",
    "imports": ["import datetime"],
    "body": """\
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[datetime.date.fromisoformat(iso_date).weekday()]""",
    "visible": [
        {"args": ["2026-09-13"], "kwargs": {}},
        {"args": ["2000-01-01"], "kwargs": {}},
        {"args": ["1999-12-31"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["2024-02-29"], "kwargs": {}},
        {"args": ["1970-01-01"], "kwargs": {}},
        {"args": ["2026-01-01"], "kwargs": {}},
        {"args": ["2026-12-25"], "kwargs": {}},
        {"args": ["2100-03-01"], "kwargs": {}},
        {"args": ["1900-02-28"], "kwargs": {}},
        {"args": ["2016-08-15"], "kwargs": {}},
        {"args": ["2020-11-03"], "kwargs": {}},
        {"args": ["1984-06-07"], "kwargs": {}},
        {"args": ["2026-09-14"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["2023-04-17"], "kwargs": {}},
        {"args": ["2011-07-04"], "kwargs": {}},
        {"args": ["2030-05-20"], "kwargs": {}},
        {"args": ["1955-11-05"], "kwargs": {}},
        {"args": ["2044-02-29"], "kwargs": {}},
        {"args": ["2008-10-31"], "kwargs": {}},
        {"args": ["1967-03-02"], "kwargs": {}},
        {"args": ["2099-12-31"], "kwargs": {}},
        {"args": ["2002-06-18"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t05_parse_duration",
    "function": "parse_duration",
    "title": "Parse a duration string into seconds",
    "category": "string",
    "return_type": "int",
    "signature": "parse_duration(text: str) -> int",
    "doc": "Convert a space-separated duration string to a total number of seconds.",
    "description": """\
Convert the duration string `text` into a whole number of seconds.

- `text` holds zero or more parts separated by whitespace, for example
  `"1h 30m"`.
- Each part is one or more decimal digits followed by a single unit letter:
  `d` = 86400 seconds, `h` = 3600, `m` = 60, `s` = 1.
- Return the sum of all parts, as an `int`.
- Parts may appear in any order, and a unit may appear more than once; repeated
  units are simply added together (`"1h 1h"` is 7200).
- A string that is empty or only whitespace returns `0`.
- The input is always well formed. You do not need to validate it.""",
    "body": """\
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0
    for part in text.split():
        total += int(part[:-1]) * units[part[-1]]
    return total""",
    "visible": [
        {"args": ["1h 30m"], "kwargs": {}},
        {"args": ["45s"], "kwargs": {}},
        {"args": ["2d 3h 4m 5s"], "kwargs": {}},
    ],
    "hidden": [
        {"args": [""], "kwargs": {}},
        {"args": ["1s"], "kwargs": {}},
        {"args": ["60s"], "kwargs": {}},
        {"args": ["90m"], "kwargs": {}},
        {"args": ["1d"], "kwargs": {}},
        {"args": ["3h 15m"], "kwargs": {}},
        {"args": ["10m 30s"], "kwargs": {}},
        {"args": ["1h 1h"], "kwargs": {}},
        {"args": ["5d 5s"], "kwargs": {}},
        {"args": ["100s"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["7h"], "kwargs": {}},
        {"args": ["25m"], "kwargs": {}},
        {"args": ["2h 45m"], "kwargs": {}},
        {"args": ["1d 12h"], "kwargs": {}},
        {"args": ["36s"], "kwargs": {}},
        {"args": ["4m 4s"], "kwargs": {}},
        {"args": ["8d"], "kwargs": {}},
        {"args": ["3h 3m 3s"], "kwargs": {}},
        {"args": ["15m 90s"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t06_chunk_list",
    "function": "chunk_list",
    "title": "Chunk a list into fixed-size pieces",
    "category": "list",
    "return_type": "list",
    "signature": "chunk_list(items: list, size: int) -> list",
    "doc": "Split a list into consecutive sublists of at most `size` elements.",
    "description": """\
Split `items` into consecutive chunks of `size` elements.

- Return a list of lists. Read `items` left to right, taking `size` elements at
  a time; the elements keep their original order.
- The final chunk is shorter than `size` when the length of `items` is not a
  multiple of `size`.
- `size` is always an integer of 1 or more. You do not need to validate it.
- If `items` is empty, return an empty list `[]` (not a list holding an empty
  list).
- If `size` is larger than the length of `items`, return a single chunk holding
  every element.""",
    "body": """\
    chunks = []
    for start in range(0, len(items), size):
        chunks.append(items[start:start + size])
    return chunks""",
    "visible": [
        {"args": [[1, 2, 3, 4, 5], 2], "kwargs": {}},
        {"args": [["a", "b", "c"], 3], "kwargs": {}},
        {"args": [[], 4], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[1, 2, 3], 1], "kwargs": {}},
        {"args": [[1, 2, 3, 4, 5, 6, 7], 3], "kwargs": {}},
        {"args": [[1], 5], "kwargs": {}},
        {"args": [[1, 2], 2], "kwargs": {}},
        {"args": [[10, 20, 30, 40], 3], "kwargs": {}},
        {"args": [["x", "y", "z", "w", "v"], 2], "kwargs": {}},
        {"args": [[True, False, True], 2], "kwargs": {}},
        {"args": [[0, 0, 0, 0, 0, 0], 4], "kwargs": {}},
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5], "kwargs": {}},
        {"args": [[[1], [2], [3]], 2], "kwargs": {}},
    ],
    "probes": [
        {"args": [[5, 6, 7, 8], 2], "kwargs": {}},
        {"args": [[9], 1], "kwargs": {}},
        {"args": [[1, 2, 3, 4, 5], 4], "kwargs": {}},
        {"args": [["p", "q"], 1], "kwargs": {}},
        {"args": [[], 1], "kwargs": {}},
        {"args": [[100, 200, 300], 10], "kwargs": {}},
        {"args": [[2, 4, 6, 8, 10, 12], 3], "kwargs": {}},
        {"args": [[1, 1, 2, 3, 5, 8, 13], 2], "kwargs": {}},
        {"args": [["alpha", "beta", "gamma", "delta"], 3], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t07_merge_intervals",
    "function": "merge_intervals",
    "title": "Merge overlapping intervals",
    "category": "list",
    "return_type": "list",
    "signature": "merge_intervals(intervals: list) -> list",
    "doc": "Merge overlapping or touching closed integer intervals.",
    "description": """\
Merge the closed intervals in `intervals`.

- Each element of `intervals` is a two-element list `[start, end]` of integers
  with `start <= end`. The input is not necessarily sorted.
- Two intervals are merged when they overlap **or** merely touch: `[1, 3]` and
  `[3, 5]` merge into `[1, 5]`, while `[1, 2]` and `[3, 4]` do not merge.
- A merged interval runs from the smallest start to the largest end of the
  intervals that went into it.
- Return a list of two-element lists, sorted by start ascending. Use lists, not
  tuples.
- An empty input returns an empty list `[]`.
- Do not modify the input list.""",
    "body": """\
    merged = []
    for start, end in sorted(intervals, key=lambda pair: (pair[0], pair[1])):
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1][1] = end
        else:
            merged.append([start, end])
    return merged""",
    "visible": [
        {"args": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "kwargs": {}},
        {"args": [[[1, 4], [4, 5]]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[[1, 2]]], "kwargs": {}},
        {"args": [[[5, 7], [1, 3]]], "kwargs": {}},
        {"args": [[[1, 10], [2, 3], [4, 5]]], "kwargs": {}},
        {"args": [[[0, 0], [0, 0]]], "kwargs": {}},
        {"args": [[[1, 2], [3, 4]]], "kwargs": {}},
        {"args": [[[-5, -1], [-2, 3]]], "kwargs": {}},
        {"args": [[[2, 3], [1, 5], [6, 9], [8, 12]]], "kwargs": {}},
        {"args": [[[7, 8]]], "kwargs": {}},
        {"args": [[[1, 1], [2, 2], [3, 3]]], "kwargs": {}},
        {"args": [[[10, 20], [20, 30], [30, 40]]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[[4, 6], [5, 9]]], "kwargs": {}},
        {"args": [[[100, 200], [150, 250], [300, 400]]], "kwargs": {}},
        {"args": [[[-3, 0]]], "kwargs": {}},
        {"args": [[[9, 9]]], "kwargs": {}},
        {"args": [[[1, 3], [5, 7], [2, 4]]], "kwargs": {}},
        {"args": [[[0, 100], [10, 20]]], "kwargs": {}},
        {"args": [[[3, 5], [1, 2]]], "kwargs": {}},
        {"args": [[[12, 15], [15, 15]]], "kwargs": {}},
        {"args": [[[6, 7], [8, 9], [7, 8]]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t08_caesar_shift",
    "function": "caesar_shift",
    "title": "Caesar shift a string",
    "category": "string",
    "return_type": "str",
    "signature": "caesar_shift(text: str, shift: int) -> str",
    "doc": "Shift the ASCII letters of a string by a given number of positions.",
    "description": """\
Apply a Caesar shift of `shift` positions to `text`.

- Shift each ASCII letter forward through the alphabet, wrapping from `z` back
  to `a` and from `Z` back to `A`.
- Case is preserved: lowercase letters stay lowercase, uppercase stay
  uppercase.
- Every character that is not an ASCII letter (digits, spaces, punctuation,
  anything else) is copied through unchanged.
- `shift` may be `0`, negative, or larger than 26; reduce it modulo 26, so a
  shift of 27 behaves like a shift of 1 and a shift of -1 behaves like a shift
  of 25.""",
    "body": """\
    step = shift % 26
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + step) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + step) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)""",
    "visible": [
        {"args": ["abc", 1], "kwargs": {}},
        {"args": ["Hello, World!", 3], "kwargs": {}},
        {"args": ["xyz", 3], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["abc", 0], "kwargs": {}},
        {"args": ["abc", 26], "kwargs": {}},
        {"args": ["abc", -1], "kwargs": {}},
        {"args": ["ABC", 2], "kwargs": {}},
        {"args": ["Zebra", 1], "kwargs": {}},
        {"args": ["attack at dawn", 13], "kwargs": {}},
        {"args": ["Python 3.12", 5], "kwargs": {}},
        {"args": ["", 7], "kwargs": {}},
        {"args": ["aA zZ", 1], "kwargs": {}},
        {"args": ["shift me 100", 100], "kwargs": {}},
    ],
    "probes": [
        {"args": ["quick brown fox", 4], "kwargs": {}},
        {"args": ["Gamma", 7], "kwargs": {}},
        {"args": ["nop", -3], "kwargs": {}},
        {"args": ["MIXED case 42", 11], "kwargs": {}},
        {"args": ["wrap around zZ", 2], "kwargs": {}},
        {"args": ["k", 25], "kwargs": {}},
        {"args": ["Tally-ho!", 6], "kwargs": {}},
        {"args": ["", 0], "kwargs": {}},
        {"args": ["digits 0123", 9], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t09_vowel_counts",
    "function": "vowel_counts",
    "title": "Count vowels in each word",
    "category": "string",
    "return_type": "dict",
    "signature": "vowel_counts(text: str) -> dict",
    "doc": "Map each whitespace-separated word to its number of vowels.",
    "description": """\
Count the vowels in every word of `text`.

- Split `text` on runs of whitespace; the words are the non-empty pieces.
- The vowels are `a`, `e`, `i`, `o`, `u`, matched case-insensitively. `y` is
  **not** a vowel.
- Return a dictionary whose keys are the words exactly as they appear in `text`
  (original case, punctuation kept) and whose values are the integer vowel
  counts for those words.
- A word that appears more than once produces one key.
- Key order does not matter.
- Text that is empty or only whitespace returns an empty dictionary `{}`.""",
    "body": """\
    counts = {}
    for word in text.split():
        counts[word] = sum(1 for ch in word.lower() if ch in "aeiou")
    return counts""",
    "visible": [
        {"args": ["hello world"], "kwargs": {}},
        {"args": ["rhythm"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["a e i o u"], "kwargs": {}},
        {"args": ["The Quick Brown Fox"], "kwargs": {}},
        {"args": ["  spaced   words  "], "kwargs": {}},
        {"args": ["AEIOU"], "kwargs": {}},
        {"args": ["Yes yes"], "kwargs": {}},
        {"args": ["banana split"], "kwargs": {}},
        {"args": ["xyz"], "kwargs": {}},
        {"args": ["Python"], "kwargs": {}},
        {"args": ["one one two"], "kwargs": {}},
        {"args": ["Mississippi river"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["coffee break"], "kwargs": {}},
        {"args": ["GIRAFFE"], "kwargs": {}},
        {"args": ["sky"], "kwargs": {}},
        {"args": ["beautiful day"], "kwargs": {}},
        {"args": ["queue"], "kwargs": {}},
        {"args": ["Umbrella"], "kwargs": {}},
        {"args": ["zzz zzz"], "kwargs": {}},
        {"args": ["Ohio"], "kwargs": {}},
        {"args": ["read the manual"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t10_median",
    "function": "median",
    "title": "Median of a list of numbers",
    "category": "number",
    "return_type": "float",
    "signature": "median(values: list) -> float",
    "doc": "Return the median of a list of numbers as a float.",
    "description": """\
Return the median of the numbers in `values`.

- Sort the values ascending. The input is not necessarily sorted and may hold
  repeats, negative numbers, ints and floats.
- If the count of values is odd, the median is the middle value.
- If the count is even, the median is the arithmetic mean of the two middle
  values.
- If `values` is empty, return `0.0`.
- Always return a `float`, so the median of `[3, 1, 2]` is `2.0`, not `2`.
- Do not round the result.
- Do not modify the input list.""",
    "body": """\
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2""",
    "visible": [
        {"args": [[3, 1, 2]], "kwargs": {}},
        {"args": [[4, 1, 3, 2]], "kwargs": {}},
        {"args": [[7]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[]], "kwargs": {}},
        {"args": [[1, 2]], "kwargs": {}},
        {"args": [[5, 5, 5]], "kwargs": {}},
        {"args": [[10, 2, 38, 23, 38, 23, 21]], "kwargs": {}},
        {"args": [[-1, -2, -3]], "kwargs": {}},
        {"args": [[0, 0, 0, 0]], "kwargs": {}},
        {"args": [[1.5, 2.5]], "kwargs": {}},
        {"args": [[100]], "kwargs": {}},
        {"args": [[2, 4, 6, 8, 10]], "kwargs": {}},
        {"args": [[9, 1, 8, 2, 7, 3]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[6, 2, 9]], "kwargs": {}},
        {"args": [[1, 2, 3, 4]], "kwargs": {}},
        {"args": [[12.5]], "kwargs": {}},
        {"args": [[-5, 0, 5, 10]], "kwargs": {}},
        {"args": [[3, 3, 3, 3, 3]], "kwargs": {}},
        {"args": [[1000, 1]], "kwargs": {}},
        {"args": [[2.25, 4.75, 6.5]], "kwargs": {}},
        {"args": [[8, 6, 7, 5, 3, 0, 9]], "kwargs": {}},
        {"args": [[0.5, 1.5, 2.5, 3.5]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t11_normalize_whitespace",
    "function": "normalize_whitespace",
    "title": "Normalise whitespace in a string",
    "category": "string",
    "return_type": "str",
    "signature": "normalize_whitespace(text: str) -> str",
    "doc": "Collapse every run of whitespace to a single space and trim the ends.",
    "description": """\
Normalise the whitespace in `text`.

- Replace every run of one or more whitespace characters (spaces, tabs,
  newlines, carriage returns, form feeds) with a single space `" "`.
- Remove all leading and trailing whitespace.
- Leave every non-whitespace character exactly as it is; do not change case and
  do not touch punctuation.
- A string that is empty or holds only whitespace returns the empty string
  `""`.""",
    "body": """\
    parts = text.split()
    if not parts:
        return ""
    return " ".join(parts)""",
    "visible": [
        {"args": ["  hello   world  "], "kwargs": {}},
        {"args": ["a\tb\nc"], "kwargs": {}},
        {"args": ["   "], "kwargs": {}},
    ],
    "hidden": [
        {"args": [""], "kwargs": {}},
        {"args": ["one"], "kwargs": {}},
        {"args": ["  leading"], "kwargs": {}},
        {"args": ["trailing  "], "kwargs": {}},
        {"args": ["multiple     spaces     here"], "kwargs": {}},
        {"args": ["\n\n\n"], "kwargs": {}},
        {"args": ["tab\tseparated\tvalues"], "kwargs": {}},
        {"args": ["mixed \t\n whitespace"], "kwargs": {}},
        {"args": ["no-change-needed"], "kwargs": {}},
        {"args": [" a  b   c    d "], "kwargs": {}},
    ],
    "probes": [
        {"args": ["  Whitespace  Galore  "], "kwargs": {}},
        {"args": ["single"], "kwargs": {}},
        {"args": ["\t\t"], "kwargs": {}},
        {"args": ["line one\nline two"], "kwargs": {}},
        {"args": ["  padded sentence here  "], "kwargs": {}},
        {"args": ["x  y"], "kwargs": {}},
        {"args": ["\n  start with newline"], "kwargs": {}},
        {"args": ["many\t\ttabs\t\there"], "kwargs": {}},
        {"args": ["   trim me   "], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t12_camel_to_snake",
    "function": "camel_to_snake",
    "title": "camelCase to snake_case",
    "category": "string",
    "return_type": "str",
    "signature": "camel_to_snake(name: str) -> str",
    "doc": "Convert a camelCase or PascalCase identifier to snake_case.",
    "description": """\
Convert the identifier `name` to snake_case.

- `name` holds only ASCII letters and digits. You do not need to validate it.
- Insert an underscore `_` immediately before every uppercase letter **except**
  an uppercase letter at index 0, then lowercase the whole string.
- Apply that rule one letter at a time, so a run of capitals gets one
  underscore per capital: `"parseXMLFile"` becomes `"parse_x_m_l_file"`.
- Digits are copied through unchanged and never get an underscore of their own.
- The empty string returns the empty string `""`.""",
    "body": """\
    out = []
    for index, ch in enumerate(name):
        if ch.isupper() and index > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)""",
    "visible": [
        {"args": ["camelCase"], "kwargs": {}},
        {"args": ["PascalCase"], "kwargs": {}},
        {"args": ["parseXMLFile"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["a"], "kwargs": {}},
        {"args": ["A"], "kwargs": {}},
        {"args": ["simpleName"], "kwargs": {}},
        {"args": ["ID"], "kwargs": {}},
        {"args": ["userID"], "kwargs": {}},
        {"args": ["myVar2Name"], "kwargs": {}},
        {"args": ["lowercase"], "kwargs": {}},
        {"args": ["ABC"], "kwargs": {}},
        {"args": ["getHTTPResponseCode"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
    ],
    "probes": [
        {"args": ["toJSON"], "kwargs": {}},
        {"args": ["FooBar"], "kwargs": {}},
        {"args": ["readFileSync"], "kwargs": {}},
        {"args": ["z"], "kwargs": {}},
        {"args": ["Q"], "kwargs": {}},
        {"args": ["aB"], "kwargs": {}},
        {"args": ["valueOfPI"], "kwargs": {}},
        {"args": ["snakeReady"], "kwargs": {}},
        {"args": ["XYZabc"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t13_validate_isbn10",
    "function": "validate_isbn10",
    "title": "Validate an ISBN-10",
    "category": "string",
    "return_type": "bool",
    "signature": "validate_isbn10(code: str) -> bool",
    "doc": "Return True when a string is a valid ISBN-10.",
    "description": """\
Decide whether `code` is a valid ISBN-10.

- First remove every hyphen `-` and every space from `code`.
- What is left must be exactly 10 characters, otherwise return `False`.
- The first 9 characters must be decimal digits. The 10th may be a decimal
  digit or the letter `X` (upper or lower case), which stands for the value 10.
  Anything else returns `False`.
- Multiply the value of the character at index `i` (counting from 0 on the
  left) by `10 - i` and add the ten products together.
- Return `True` when that total is divisible by 11, otherwise `False`.
- Return a real `bool` (`True` / `False`), not `1` / `0`.""",
    "body": """\
    cleaned = code.replace("-", "").replace(" ", "")
    if len(cleaned) != 10:
        return False
    total = 0
    for index, ch in enumerate(cleaned):
        if ch.isdigit():
            value = int(ch)
        elif ch in "Xx" and index == 9:
            value = 10
        else:
            return False
        total += value * (10 - index)
    return total % 11 == 0""",
    "visible": [
        {"args": ["0306406152"], "kwargs": {}},
        {"args": ["0306406153"], "kwargs": {}},
        {"args": ["043942089X"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["0-306-40615-2"], "kwargs": {}},
        {"args": ["030640615X"], "kwargs": {}},
        {"args": ["123456789"], "kwargs": {}},
        {"args": ["12345678901"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
        {"args": ["0000000000"], "kwargs": {}},
        {"args": ["X123456789"], "kwargs": {}},
        {"args": ["080442957X"], "kwargs": {}},
        {"args": ["0-19-852663-6"], "kwargs": {}},
        {"args": ["043942089x"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["0131103628"], "kwargs": {}},
        {"args": ["0131103629"], "kwargs": {}},
        {"args": ["0471958697"], "kwargs": {}},
        {"args": ["99921-58-10-7"], "kwargs": {}},
        {"args": ["85-359-0277-5"], "kwargs": {}},
        {"args": ["12345"], "kwargs": {}},
        {"args": ["0X0000000X"], "kwargs": {}},
        {"args": ["9999999999"], "kwargs": {}},
        {"args": ["111111111X"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t14_luhn_check_digit",
    "function": "luhn_check_digit",
    "title": "Luhn check digit",
    "category": "number",
    "return_type": "int",
    "signature": "luhn_check_digit(digits: str) -> int",
    "doc": "Compute the Luhn check digit for a string of payload digits.",
    "description": """\
Compute the Luhn check digit for the payload `digits`.

- `digits` holds only decimal digit characters and does **not** include the
  check digit. It may be empty. You do not need to validate it.
- Walk the payload from right to left, numbering the digits 1, 2, 3, ... .
- Double every digit in an odd position of that walk (the 1st, 3rd, 5th, ...
  from the right); if a doubled value is greater than 9, subtract 9 from it.
- Leave the digits in even positions alone.
- Add all the resulting values together to get `total`.
- Return `(10 - total % 10) % 10` as an `int` in the range 0-9.
- An empty payload gives `0`.""",
    "body": """\
    total = 0
    for index, ch in enumerate(reversed(digits)):
        value = int(ch)
        if index % 2 == 0:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return (10 - total % 10) % 10""",
    "visible": [
        {"args": ["7992739871"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
        {"args": ["1"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["0"], "kwargs": {}},
        {"args": ["00000000"], "kwargs": {}},
        {"args": ["123456789"], "kwargs": {}},
        {"args": ["453201511283036"], "kwargs": {}},
        {"args": ["9"], "kwargs": {}},
        {"args": ["411111111111111"], "kwargs": {}},
        {"args": ["555555555555444"], "kwargs": {}},
        {"args": ["12"], "kwargs": {}},
        {"args": ["999999999999999"], "kwargs": {}},
        {"args": ["378282246310000"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["79927398712"], "kwargs": {}},
        {"args": ["1234"], "kwargs": {}},
        {"args": ["8"], "kwargs": {}},
        {"args": ["5105105105105"], "kwargs": {}},
        {"args": ["6011111111111"], "kwargs": {}},
        {"args": ["42"], "kwargs": {}},
        {"args": ["000000000001"], "kwargs": {}},
        {"args": ["987654321"], "kwargs": {}},
        {"args": ["3056930902590"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t15_group_anagrams",
    "function": "group_anagrams",
    "title": "Group anagrams together",
    "category": "list",
    "return_type": "list",
    "signature": "group_anagrams(words: list) -> list",
    "doc": "Group words that are anagrams of one another, in sorted order.",
    "description": """\
Group the strings in `words` into sets of anagrams.

- Two words are anagrams when one is a rearrangement of the other, comparing
  characters exactly: the test is **case-sensitive**, so `"Dog"` and `"god"`
  are not anagrams and belong to different groups.
- Every word of the input belongs to exactly one group. A word repeated in the
  input appears that many times in its group.
- Sort the words inside each group ascending with Python's default string
  ordering (`sorted`).
- Sort the groups ascending by their first word.
- Return a list of lists of strings. An empty input returns an empty list
  `[]`.""",
    "body": """\
    groups = {}
    for word in words:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    result = [sorted(group) for group in groups.values()]
    result.sort()
    return result""",
    "visible": [
        {"args": [["eat", "tea", "tan", "ate", "nat", "bat"]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
        {"args": [["abc"]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [["listen", "silent", "enlist"]], "kwargs": {}},
        {"args": [["a", "b", "a"]], "kwargs": {}},
        {"args": [["Dog", "god"]], "kwargs": {}},
        {"args": [["", ""]], "kwargs": {}},
        {"args": [["rat", "tar", "art", "star"]], "kwargs": {}},
        {"args": [["one"]], "kwargs": {}},
        {"args": [["ab", "ba", "abc", "cba", "bca"]], "kwargs": {}},
        {"args": [["xy", "xy", "yx"]], "kwargs": {}},
        {"args": [["hello"]], "kwargs": {}},
        {"args": [["stop", "tops", "pots", "opts", "spot"]], "kwargs": {}},
    ],
    "probes": [
        {"args": [["cat", "act", "tac"]], "kwargs": {}},
        {"args": [["night", "thing"]], "kwargs": {}},
        {"args": [["z"]], "kwargs": {}},
        {"args": [["pea", "ape", "pae"]], "kwargs": {}},
        {"args": [["Listen", "Silent"]], "kwargs": {}},
        {"args": [["abcd", "dcba", "bcda"]], "kwargs": {}},
        {"args": [["dusty", "study"]], "kwargs": {}},
        {"args": [["po", "op", "po"]], "kwargs": {}},
        {"args": [["evil", "vile", "live", "veil"]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t16_top_k_tokens",
    "function": "top_k_tokens",
    "title": "Top k most frequent tokens",
    "category": "string",
    "return_type": "list",
    "signature": "top_k_tokens(text: str, k: int) -> list",
    "doc": "Return the k most frequent lowercase tokens, ties broken alphabetically.",
    "description": """\
Return the `k` most frequent tokens of `text`.

- Lowercase `text`, then split it on runs of whitespace; the tokens are the
  non-empty pieces. Punctuation stays attached to its token.
- Count how often each distinct token occurs.
- Order the distinct tokens by count descending; break ties by the token
  itself, ascending, using Python's default string ordering.
- Return the first `k` tokens of that order, as a list of strings (the counts
  are not returned).
- If `k` is larger than the number of distinct tokens, return all of them.
- `k` is always 0 or more; `k = 0` returns an empty list `[]`.""",
    "body": """\
    counts = {}
    for token in text.lower().split():
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [token for token, _count in ranked[:k]]""",
    "visible": [
        {"args": ["the cat the dog the bird", 2], "kwargs": {}},
        {"args": ["a b c", 5], "kwargs": {}},
        {"args": ["", 3], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["one two two three three three", 3], "kwargs": {}},
        {"args": ["Apple apple APPLE", 1], "kwargs": {}},
        {"args": ["x y z", 0], "kwargs": {}},
        {"args": ["repeat repeat", 5], "kwargs": {}},
        {"args": ["alpha beta gamma delta", 2], "kwargs": {}},
        {"args": ["  spaced   words  ", 1], "kwargs": {}},
        {"args": ["hello", 1], "kwargs": {}},
        {"args": ["a a b b c c", 2], "kwargs": {}},
        {"args": ["to be or not to be", 2], "kwargs": {}},
        {"args": ["Mixed CASE mixed case", 2], "kwargs": {}},
    ],
    "probes": [
        {"args": ["red blue red green blue red", 2], "kwargs": {}},
        {"args": ["solo", 5], "kwargs": {}},
        {"args": ["one", 0], "kwargs": {}},
        {"args": ["dog cat dog cat bird", 3], "kwargs": {}},
        {"args": ["SAME same SaMe other", 1], "kwargs": {}},
        {"args": ["p q r s t", 3], "kwargs": {}},
        {"args": ["many many many few few one", 2], "kwargs": {}},
        {"args": ["tie tie break break", 2], "kwargs": {}},
        {"args": ["   ", 4], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t17_format_bytes",
    "function": "format_bytes",
    "title": "Human-readable byte size",
    "category": "number",
    "return_type": "str",
    "signature": "format_bytes(count: int) -> str",
    "doc": "Format a byte count using binary units B, KB, MB, GB, TB.",
    "description": """\
Format the byte count `count` for a human reader.

- `count` is an integer of 0 or more.
- The units are `B`, `KB`, `MB`, `GB`, `TB`, each 1024 times the one before it.
- Start at `B` and, while the value is 1024 or more and a larger unit is still
  available, divide it by 1024 and step up one unit. `TB` is the largest unit,
  so very large counts stay in `TB` (1125899906842624 is `"1024.0 TB"`).
- If the chosen unit is `B`, return the integer count, a single space, then
  `B`, for example `"512 B"` - no decimal point.
- For every other unit return the divided value formatted to exactly one
  decimal place (Python's `f"{value:.1f}"`), a single space, then the unit, for
  example `"1.5 KB"`.""",
    "body": """\
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(count)
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return "{} {}".format(count, units[0])
    return "{:.1f} {}".format(value, units[index])""",
    "visible": [
        {"args": [0], "kwargs": {}},
        {"args": [1024], "kwargs": {}},
        {"args": [1536], "kwargs": {}},
    ],
    "hidden": [
        {"args": [1], "kwargs": {}},
        {"args": [1023], "kwargs": {}},
        {"args": [1048576], "kwargs": {}},
        {"args": [1073741824], "kwargs": {}},
        {"args": [1099511627776], "kwargs": {}},
        {"args": [5242880], "kwargs": {}},
        {"args": [2560], "kwargs": {}},
        {"args": [999], "kwargs": {}},
        {"args": [1125899906842624], "kwargs": {}},
        {"args": [123456789], "kwargs": {}},
        {"args": [4096], "kwargs": {}},
    ],
    "probes": [
        {"args": [512], "kwargs": {}},
        {"args": [2048], "kwargs": {}},
        {"args": [3145728], "kwargs": {}},
        {"args": [1500], "kwargs": {}},
        {"args": [10240], "kwargs": {}},
        {"args": [2147483648], "kwargs": {}},
        {"args": [7], "kwargs": {}},
        {"args": [987654321], "kwargs": {}},
        {"args": [16777216], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t18_business_days",
    "function": "business_days",
    "title": "Business days between two dates",
    "category": "date",
    "return_type": "int",
    "signature": "business_days(start_iso: str, end_iso: str) -> int",
    "doc": "Count Monday-to-Friday days in an inclusive ISO date range.",
    "description": """\
Count the business days from `start_iso` to `end_iso`.

- Both arguments are valid dates in `YYYY-MM-DD` form. You do not need to
  validate them.
- The range is **inclusive at both ends**: both the start date and the end date
  are counted when they are business days.
- A business day is any day from Monday to Friday. Saturday and Sunday are not
  counted.
- Public holidays are ignored; only the weekday matters.
- If `end_iso` is earlier than `start_iso`, return `0`.""",
    "imports": ["import datetime"],
    "body": """\
    start = datetime.date.fromisoformat(start_iso)
    end = datetime.date.fromisoformat(end_iso)
    if end < start:
        return 0
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += datetime.timedelta(days=1)
    return count""",
    "visible": [
        {"args": ["2026-09-14", "2026-09-18"], "kwargs": {}},
        {"args": ["2026-09-12", "2026-09-13"], "kwargs": {}},
        {"args": ["2026-09-14", "2026-09-14"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["2026-01-01", "2026-01-31"], "kwargs": {}},
        {"args": ["2026-09-18", "2026-09-14"], "kwargs": {}},
        {"args": ["2024-02-26", "2024-03-01"], "kwargs": {}},
        {"args": ["2026-12-25", "2026-12-25"], "kwargs": {}},
        {"args": ["2000-01-01", "2000-12-31"], "kwargs": {}},
        {"args": ["2026-09-13", "2026-09-13"], "kwargs": {}},
        {"args": ["2026-09-14", "2026-09-20"], "kwargs": {}},
        {"args": ["1999-12-31", "2000-01-03"], "kwargs": {}},
        {"args": ["2026-06-01", "2026-06-05"], "kwargs": {}},
        {"args": ["2026-02-28", "2026-03-02"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["2026-03-02", "2026-03-13"], "kwargs": {}},
        {"args": ["2025-11-27", "2025-11-28"], "kwargs": {}},
        {"args": ["2026-07-04", "2026-07-04"], "kwargs": {}},
        {"args": ["2026-04-01", "2026-04-30"], "kwargs": {}},
        {"args": ["2023-05-15", "2023-05-19"], "kwargs": {}},
        {"args": ["2026-08-31", "2026-09-04"], "kwargs": {}},
        {"args": ["2026-10-10", "2026-10-11"], "kwargs": {}},
        {"args": ["2026-05-01", "2026-04-01"], "kwargs": {}},
        {"args": ["2021-01-04", "2021-01-15"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t19_flatten",
    "function": "flatten",
    "title": "Flatten a nested list",
    "category": "list",
    "return_type": "list",
    "signature": "flatten(items: list) -> list",
    "doc": "Flatten arbitrarily nested lists into a single flat list.",
    "description": """\
Flatten the nested list `items` completely.

- Walk `items` left to right. Every element that is itself a list is flattened
  in place, to any depth; every other element is copied through unchanged.
- The relative order of the non-list elements is preserved.
- Nested empty lists contribute nothing, so `[[], []]` flattens to `[]`.
- Only `list` counts as a nested container; strings are ordinary elements and
  are never split into characters.
- Return a new list; do not modify the input.""",
    "body": """\
    out = []
    for item in items:
        if isinstance(item, list):
            out.extend(flatten(item))
        else:
            out.append(item)
    return out""",
    "visible": [
        {"args": [[1, [2, 3], [4, [5]]]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
        {"args": [[[[["deep"]]]]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[1, 2, 3]], "kwargs": {}},
        {"args": [[[], [], []]], "kwargs": {}},
        {"args": [[[1], [2], [3]]], "kwargs": {}},
        {"args": [[1, [2, [3, [4, [5]]]]]], "kwargs": {}},
        {"args": [[["a", ["b"]], "c"]], "kwargs": {}},
        {"args": [[[]]], "kwargs": {}},
        {"args": [[0, [False, [None]]]], "kwargs": {}},
        {"args": [[[1, 2], [], [3]]], "kwargs": {}},
        {"args": [["x"]], "kwargs": {}},
        {"args": [[[[1]], [[2]], [[3]]]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[7, [8, [9]]]], "kwargs": {}},
        {"args": [[["p"], ["q"], ["r"]]], "kwargs": {}},
        {"args": [[[[[]]]]], "kwargs": {}},
        {"args": [[1, [2], 3, [4], 5]], "kwargs": {}},
        {"args": [[[["nested"], "mid"], "outer"]], "kwargs": {}},
        {"args": [[[10, [20, [30, [40]]]]]], "kwargs": {}},
        {"args": [[[], [1], [], [2]]], "kwargs": {}},
        {"args": [["solo"]], "kwargs": {}},
        {"args": [[[True, [False]], True]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t20_avg_word_length",
    "function": "avg_word_length",
    "title": "Average word length",
    "category": "string",
    "return_type": "float",
    "signature": "avg_word_length(text: str) -> float",
    "doc": "Mean length of the whitespace-separated words, rounded to two decimals.",
    "description": """\
Return the mean length of the words in `text`.

- Split `text` on runs of whitespace; the words are the non-empty pieces.
- A word's length is its number of characters; punctuation and digits count as
  characters, so `"counts!"` has length 7.
- Divide the total number of characters in all words by the number of words.
- Round the result to 2 decimal places with Python's built-in `round(x, 2)`.
- Text that is empty or holds only whitespace returns `0.0`.
- Always return a `float`.""",
    "body": """\
    words = text.split()
    if not words:
        return 0.0
    total = sum(len(word) for word in words)
    return round(total / len(words), 2)""",
    "visible": [
        {"args": ["the quick brown fox"], "kwargs": {}},
        {"args": ["hello"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["a"], "kwargs": {}},
        {"args": ["ab cd"], "kwargs": {}},
        {"args": ["one two three four five"], "kwargs": {}},
        {"args": ["   "], "kwargs": {}},
        {"args": ["Punctuation, counts!"], "kwargs": {}},
        {"args": ["I am"], "kwargs": {}},
        {"args": ["supercalifragilisticexpialidocious"], "kwargs": {}},
        {"args": ["x y z w"], "kwargs": {}},
        {"args": ["two  spaces   between"], "kwargs": {}},
        {"args": ["1234 56"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["measure these words"], "kwargs": {}},
        {"args": ["z"], "kwargs": {}},
        {"args": ["double  space"], "kwargs": {}},
        {"args": ["Hello, World!"], "kwargs": {}},
        {"args": ["a bb ccc dddd"], "kwargs": {}},
        {"args": ["  padded  "], "kwargs": {}},
        {"args": ["9 99 999"], "kwargs": {}},
        {"args": ["The rain in Spain"], "kwargs": {}},
        {"args": ["wordwithoutspaces"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t21_balanced_brackets",
    "function": "balanced_brackets",
    "title": "Balanced brackets",
    "category": "string",
    "return_type": "bool",
    "signature": "balanced_brackets(text: str) -> bool",
    "doc": "Return True when every bracket in the string is matched and nested correctly.",
    "description": """\
Decide whether the brackets in `text` are balanced.

- Only these six characters matter: `(`, `)`, `[`, `]`, `{`, `}`. Every other
  character is ignored.
- The brackets are balanced when each closing bracket matches the most recent
  unclosed opening bracket of the same kind and no bracket is left unclosed.
- `"([)]"` is **not** balanced, because the brackets cross.
- A string with no brackets at all is balanced, and so is the empty string.
- Return a real `bool` (`True` / `False`).""",
    "body": """\
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack""",
    "visible": [
        {"args": ["(a[b]{c})"], "kwargs": {}},
        {"args": ["([)]"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["()"], "kwargs": {}},
        {"args": ["("], "kwargs": {}},
        {"args": [")"], "kwargs": {}},
        {"args": ["no brackets here"], "kwargs": {}},
        {"args": ["{[()]}"], "kwargs": {}},
        {"args": ["(()"], "kwargs": {}},
        {"args": ["())"], "kwargs": {}},
        {"args": ["[a](b){c}"], "kwargs": {}},
        {"args": ["{{{}}}"], "kwargs": {}},
        {"args": [")("], "kwargs": {}},
    ],
    "probes": [
        {"args": ["[]"], "kwargs": {}},
        {"args": ["([{}])"], "kwargs": {}},
        {"args": ["(("], "kwargs": {}},
        {"args": ["]["], "kwargs": {}},
        {"args": ["a(b)c[d]e{f}"], "kwargs": {}},
        {"args": ["{[}]"], "kwargs": {}},
        {"args": ["((()))"], "kwargs": {}},
        {"args": ["plain text 123"], "kwargs": {}},
        {"args": ["(]"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t22_word_wrap",
    "function": "word_wrap",
    "title": "Wrap text at a width",
    "category": "string",
    "return_type": "list",
    "signature": "word_wrap(text: str, width: int) -> list",
    "doc": "Greedily wrap words into lines of at most `width` characters.",
    "description": """\
Wrap `text` into lines of at most `width` characters, greedily.

- Split `text` on runs of whitespace to get the words; the original line breaks
  and multiple spaces are discarded.
- Fill each line left to right: append the next word to the current line when
  the line would still be at most `width` characters long after adding one
  space and that word. Otherwise start a new line with that word.
- Words inside a line are joined by exactly one space.
- A word longer than `width` is never split: it goes on a line of its own,
  whole, even though that line is longer than `width`.
- Return the list of line strings, in order. Do not pad lines.
- `width` is always 1 or more. Text that is empty or only whitespace returns an
  empty list `[]`.""",
    "body": """\
    lines = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines""",
    "visible": [
        {"args": ["the quick brown fox jumps", 10], "kwargs": {}},
        {"args": ["", 5], "kwargs": {}},
        {"args": ["supercalifragilistic", 5], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["a b c", 1], "kwargs": {}},
        {"args": ["hello world", 11], "kwargs": {}},
        {"args": ["hello world", 10], "kwargs": {}},
        {"args": ["   ", 4], "kwargs": {}},
        {"args": ["one", 100], "kwargs": {}},
        {"args": ["aa bb cc dd", 5], "kwargs": {}},
        {"args": ["longword short", 4], "kwargs": {}},
        {"args": ["x y z w v", 3], "kwargs": {}},
        {"args": ["  padded   words  ", 20], "kwargs": {}},
        {"args": ["to be or not to be", 8], "kwargs": {}},
    ],
    "probes": [
        {"args": ["alpha beta gamma", 11], "kwargs": {}},
        {"args": ["wrap me now", 4], "kwargs": {}},
        {"args": ["single", 6], "kwargs": {}},
        {"args": ["a bb ccc dddd eeeee", 7], "kwargs": {}},
        {"args": ["   ", 1], "kwargs": {}},
        {"args": ["the rain in spain falls", 9], "kwargs": {}},
        {"args": ["verylongwordhere tiny", 8], "kwargs": {}},
        {"args": ["q", 1], "kwargs": {}},
        {"args": ["keep it short", 13], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t23_dedupe",
    "function": "dedupe",
    "title": "Remove duplicates, keeping order",
    "category": "list",
    "return_type": "list",
    "signature": "dedupe(items: list) -> list",
    "doc": "Drop repeated values while preserving first-appearance order.",
    "description": """\
Remove the duplicate values from `items`.

- `items` holds strings and numbers only. You do not need to handle other
  types.
- Keep the **first** occurrence of every distinct value and drop every later
  occurrence.
- The surviving values stay in the order in which they first appeared.
- Values are compared for equality, and strings are compared case-sensitively,
  so `"A"` and `"a"` are two different values.
- Return a new list; do not modify the input. An empty input returns `[]`.""",
    "body": """\
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out""",
    "visible": [
        {"args": [[1, 2, 1, 3, 2]], "kwargs": {}},
        {"args": [["a", "b", "a"]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[1, 1, 1]], "kwargs": {}},
        {"args": [[3, 2, 1]], "kwargs": {}},
        {"args": [["x"]], "kwargs": {}},
        {"args": [[0, 0, 1, 1, 0]], "kwargs": {}},
        {"args": [["dog", "cat", "dog", "bird", "cat"]], "kwargs": {}},
        {"args": [[5]], "kwargs": {}},
        {"args": [[1, 2, 3, 4, 5]], "kwargs": {}},
        {"args": [[-1, -1, 2, -1]], "kwargs": {}},
        {"args": [["A", "a", "A"]], "kwargs": {}},
        {"args": [[10, 20, 10, 30, 20, 40]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[7, 7, 8]], "kwargs": {}},
        {"args": [["red", "green", "red", "blue"]], "kwargs": {}},
        {"args": [[9, 8, 9, 7, 8]], "kwargs": {}},
        {"args": [["only"]], "kwargs": {}},
        {"args": [[2, 2, 2, 2, 2]], "kwargs": {}},
        {"args": [[100, 200, 300]], "kwargs": {}},
        {"args": [["m", "n", "m", "n", "m"]], "kwargs": {}},
        {"args": [[0]], "kwargs": {}},
        {"args": [[4, 5, 6, 4, 5, 6, 7]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t24_transpose",
    "function": "transpose",
    "title": "Transpose a matrix",
    "category": "list",
    "return_type": "list",
    "signature": "transpose(matrix: list) -> list",
    "doc": "Swap the rows and columns of a rectangular matrix.",
    "description": """\
Transpose the rectangular matrix `matrix`.

- `matrix` is a list of rows; every row is a list, and all rows have the same
  length. You do not need to validate that.
- The result is a list of columns: element `[i][j]` of the result is element
  `[j][i]` of the input.
- Return a list of lists. Use lists, not tuples.
- If `matrix` is empty, or every row is empty, return an empty list `[]`.
- Do not modify the input.""",
    "body": """\
    if not matrix or not matrix[0]:
        return []
    result = []
    for col in range(len(matrix[0])):
        result.append([row[col] for row in matrix])
    return result""",
    "visible": [
        {"args": [[[1, 2, 3], [4, 5, 6]]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
        {"args": [[[1], [2], [3]]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[[1]]], "kwargs": {}},
        {"args": [[[1, 2], [3, 4]]], "kwargs": {}},
        {"args": [[[], []]], "kwargs": {}},
        {"args": [[[1, 2, 3]]], "kwargs": {}},
        {"args": [[["a", "b"], ["c", "d"], ["e", "f"]]], "kwargs": {}},
        {"args": [[[0, 0], [0, 0]]], "kwargs": {}},
        {"args": [[[1, 2, 3, 4]]], "kwargs": {}},
        {"args": [[[1], [2]]], "kwargs": {}},
        {"args": [[[True, False], [False, True]]], "kwargs": {}},
        {"args": [[[10, 20, 30], [40, 50, 60], [70, 80, 90]]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[[7, 8], [9, 10]]], "kwargs": {}},
        {"args": [[[5]]], "kwargs": {}},
        {"args": [[["p", "q", "r"]]], "kwargs": {}},
        {"args": [[[1, 2], [3, 4], [5, 6]]], "kwargs": {}},
        {"args": [[[]]], "kwargs": {}},
        {"args": [[[100], [200], [300]]], "kwargs": {}},
        {"args": [[["x"], ["y"]]], "kwargs": {}},
        {"args": [[[1, 0, 1], [0, 1, 0]]], "kwargs": {}},
        {"args": [[[2, 4], [6, 8], [10, 12], [14, 16]]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t25_hex_to_rgb",
    "function": "hex_to_rgb",
    "title": "Hex colour to RGB",
    "category": "string",
    "return_type": "list",
    "signature": "hex_to_rgb(color: str) -> list",
    "doc": "Convert a hex colour string to a list of three 0-255 integers.",
    "description": """\
Convert the hex colour `color` into its red, green and blue components.

- `color` may start with a `#`; if it does, ignore that character.
- What is left is either 6 hex digits (`"0d1e2f"`) or the 3-digit shorthand
  (`"0d1"`), in upper or lower case. You do not need to validate it.
- In the shorthand form each digit is doubled first, so `"abc"` means
  `"aabbcc"`.
- Read the 6 digits as three pairs and convert each pair from base 16.
- Return a list of exactly three integers in the range 0-255, in red, green,
  blue order. Use a list, not a tuple.""",
    "body": """\
    digits = color.lstrip("#")
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    red = int(digits[0:2], 16)
    green = int(digits[2:4], 16)
    blue = int(digits[4:6], 16)
    return [red, green, blue]""",
    "visible": [
        {"args": ["#FF0000"], "kwargs": {}},
        {"args": ["00ff00"], "kwargs": {}},
        {"args": ["#abc"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["#000000"], "kwargs": {}},
        {"args": ["#FFFFFF"], "kwargs": {}},
        {"args": ["ffffff"], "kwargs": {}},
        {"args": ["#123456"], "kwargs": {}},
        {"args": ["abcdef"], "kwargs": {}},
        {"args": ["#fff"], "kwargs": {}},
        {"args": ["000"], "kwargs": {}},
        {"args": ["#0A0B0C"], "kwargs": {}},
        {"args": ["7F7F7F"], "kwargs": {}},
        {"args": ["#00FF7F"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["#4B0082"], "kwargs": {}},
        {"args": ["112233"], "kwargs": {}},
        {"args": ["#f0f"], "kwargs": {}},
        {"args": ["808080"], "kwargs": {}},
        {"args": ["#FFD700"], "kwargs": {}},
        {"args": ["0f0"], "kwargs": {}},
        {"args": ["#C0C0C0"], "kwargs": {}},
        {"args": ["1a2b3c"], "kwargs": {}},
        {"args": ["#006400"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t26_semver_compare",
    "function": "semver_compare",
    "title": "Compare two version numbers",
    "category": "string",
    "return_type": "int",
    "signature": "semver_compare(left: str, right: str) -> int",
    "doc": "Compare two MAJOR.MINOR.PATCH version strings numerically.",
    "description": """\
Compare the two version strings `left` and `right`.

- Each version is exactly three parts separated by dots,
  `MAJOR.MINOR.PATCH`, and every part is a string of decimal digits. There are
  no pre-release or build suffixes. You do not need to validate the input.
- Compare the parts **numerically**, most significant first: major, then minor,
  then patch. So `"1.10.0"` is greater than `"1.9.0"`.
- Leading zeros carry no meaning: `"1.02.0"` equals `"1.2.0"`.
- Return the `int` `-1` when `left` is lower than `right`, `0` when they are
  equal, and `1` when `left` is higher than `right`.""",
    "body": """\
    left_parts = [int(part) for part in left.split(".")]
    right_parts = [int(part) for part in right.split(".")]
    if left_parts < right_parts:
        return -1
    if left_parts > right_parts:
        return 1
    return 0""",
    "visible": [
        {"args": ["1.0.0", "1.0.1"], "kwargs": {}},
        {"args": ["1.10.0", "1.9.0"], "kwargs": {}},
        {"args": ["2.3.4", "2.3.4"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["0.0.1", "0.0.1"], "kwargs": {}},
        {"args": ["1.0.0", "0.9.9"], "kwargs": {}},
        {"args": ["0.1.0", "1.0.0"], "kwargs": {}},
        {"args": ["1.2.3", "1.2.10"], "kwargs": {}},
        {"args": ["10.0.0", "9.99.99"], "kwargs": {}},
        {"args": ["1.02.0", "1.2.0"], "kwargs": {}},
        {"args": ["0.0.0", "0.0.0"], "kwargs": {}},
        {"args": ["3.1.4", "3.1.5"], "kwargs": {}},
        {"args": ["2.0.0", "2.0.0"], "kwargs": {}},
        {"args": ["12.34.56", "12.34.55"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["1.1.1", "1.1.2"], "kwargs": {}},
        {"args": ["5.0.0", "4.9.9"], "kwargs": {}},
        {"args": ["0.10.0", "0.9.0"], "kwargs": {}},
        {"args": ["7.7.7", "7.7.7"], "kwargs": {}},
        {"args": ["1.0.10", "1.0.9"], "kwargs": {}},
        {"args": ["100.0.0", "99.999.999"], "kwargs": {}},
        {"args": ["2.5.0", "2.50.0"], "kwargs": {}},
        {"args": ["0.0.9", "0.1.0"], "kwargs": {}},
        {"args": ["8.1.0", "8.1.0"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t27_leap_years",
    "function": "leap_years",
    "title": "Count leap years in a range",
    "category": "date",
    "return_type": "int",
    "signature": "leap_years(start_year: int, end_year: int) -> int",
    "doc": "Count the Gregorian leap years in an inclusive year range.",
    "description": """\
Count the leap years from `start_year` to `end_year`.

- The range is **inclusive at both ends**: both years are examined.
- A year is a leap year when it is divisible by 4, except that a year divisible
  by 100 is not a leap year unless it is also divisible by 400. So 1900 is not
  a leap year and 2000 is.
- Both arguments are positive integers.
- If `end_year` is smaller than `start_year`, return `0`.
- Return the count as an `int`.""",
    "body": """\
    count = 0
    for year in range(start_year, end_year + 1):
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            count += 1
    return count""",
    "visible": [
        {"args": [2000, 2020], "kwargs": {}},
        {"args": [1900, 1900], "kwargs": {}},
        {"args": [2024, 2024], "kwargs": {}},
    ],
    "hidden": [
        {"args": [1, 1], "kwargs": {}},
        {"args": [1896, 1904], "kwargs": {}},
        {"args": [2000, 2000], "kwargs": {}},
        {"args": [2020, 2019], "kwargs": {}},
        {"args": [1, 100], "kwargs": {}},
        {"args": [2001, 2003], "kwargs": {}},
        {"args": [1600, 1600], "kwargs": {}},
        {"args": [1700, 1799], "kwargs": {}},
        {"args": [2000, 2400], "kwargs": {}},
        {"args": [1970, 2026], "kwargs": {}},
    ],
    "probes": [
        {"args": [1990, 2010], "kwargs": {}},
        {"args": [1800, 1800], "kwargs": {}},
        {"args": [2016, 2016], "kwargs": {}},
        {"args": [2100, 2200], "kwargs": {}},
        {"args": [1, 4], "kwargs": {}},
        {"args": [2050, 2060], "kwargs": {}},
        {"args": [1066, 1066], "kwargs": {}},
        {"args": [3, 3], "kwargs": {}},
        {"args": [1999, 2001], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t28_running_average",
    "function": "running_average",
    "title": "Running average of a list",
    "category": "number",
    "return_type": "list",
    "signature": "running_average(values: list) -> list",
    "doc": "Return the cumulative mean after each element, rounded to two decimals.",
    "description": """\
Return the running (cumulative) average of `values`.

- The result has exactly as many elements as the input.
- Element `i` of the result is the arithmetic mean of the first `i + 1` values
  of the input.
- Round every element to 2 decimal places with Python's built-in `round(x, 2)`.
- The values may be ints or floats, positive or negative; the results are
  floats.
- An empty input returns an empty list `[]`.
- Do not modify the input list.""",
    "body": """\
    averages = []
    total = 0
    for index, value in enumerate(values, start=1):
        total += value
        averages.append(round(total / index, 2))
    return averages""",
    "visible": [
        {"args": [[1, 2, 3]], "kwargs": {}},
        {"args": [[]], "kwargs": {}},
        {"args": [[10]], "kwargs": {}},
    ],
    "hidden": [
        {"args": [[0, 0, 0]], "kwargs": {}},
        {"args": [[1, 2]], "kwargs": {}},
        {"args": [[5, 5, 5, 5]], "kwargs": {}},
        {"args": [[1, 2, 3, 4, 5]], "kwargs": {}},
        {"args": [[-1, 1]], "kwargs": {}},
        {"args": [[2.5, 3.5]], "kwargs": {}},
        {"args": [[100, 0]], "kwargs": {}},
        {"args": [[1, 1, 1, 1, 1, 1]], "kwargs": {}},
        {"args": [[3, 1, 4, 1, 5]], "kwargs": {}},
        {"args": [[7, 8, 9, 10]], "kwargs": {}},
    ],
    "probes": [
        {"args": [[6, 6, 6]], "kwargs": {}},
        {"args": [[2, 4, 6, 8]], "kwargs": {}},
        {"args": [[0]], "kwargs": {}},
        {"args": [[-5, 5, -5, 5]], "kwargs": {}},
        {"args": [[1.5, 2.5, 3.5]], "kwargs": {}},
        {"args": [[9, 1]], "kwargs": {}},
        {"args": [[10, 20, 30, 40, 50]], "kwargs": {}},
        {"args": [[1, 2, 4, 8]], "kwargs": {}},
        {"args": [[0.1, 0.2, 0.3]], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t29_extract_hashtags",
    "function": "extract_hashtags",
    "title": "Extract hashtags from text",
    "category": "string",
    "return_type": "list",
    "signature": "extract_hashtags(text: str) -> list",
    "doc": "Collect the distinct lowercase hashtags of a string, in order.",
    "description": """\
Extract the hashtags from `text`.

- A hashtag is a `#` followed by one or more characters from `A-Z`, `a-z`,
  `0-9` and `_`. The hashtag ends at the first character that is not one of
  those.
- A `#` that is not followed by at least one such character is not a hashtag
  and is ignored.
- A hashtag may start anywhere in the string, including directly after another
  character.
- Return the tag text **without** the leading `#`, lowercased.
- Keep the order of first appearance and drop later duplicates, comparing the
  lowercased text (so `#Tag` and `#tag` yield one entry, `"tag"`).
- Return a list of strings; text with no hashtags returns `[]`.""",
    "imports": ["import re"],
    "body": """\
    tags = []
    for match in re.finditer(r"#([A-Za-z0-9_]+)", text):
        tag = match.group(1).lower()
        if tag not in tags:
            tags.append(tag)
    return tags""",
    "visible": [
        {"args": ["Loving #Python and #python3 today!"], "kwargs": {}},
        {"args": ["no tags here"], "kwargs": {}},
        {"args": ["#a #A #b"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["#one #two #three"], "kwargs": {}},
        {"args": ["#"], "kwargs": {}},
        {"args": ["## #x"], "kwargs": {}},
        {"args": ["text #Tag, more #tag."], "kwargs": {}},
        {"args": [""], "kwargs": {}},
        {"args": ["#123"], "kwargs": {}},
        {"args": ["#with_underscore"], "kwargs": {}},
        {"args": ["a#b c#d"], "kwargs": {}},
        {"args": ["#MixedCase #mixedcase"], "kwargs": {}},
        {"args": ["#end"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["#alpha #Beta #GAMMA"], "kwargs": {}},
        {"args": ["nothing"], "kwargs": {}},
        {"args": ["#x1 #x2 #x1"], "kwargs": {}},
        {"args": ["#_private"], "kwargs": {}},
        {"args": ["#tag!"], "kwargs": {}},
        {"args": ["he said #Hello there"], "kwargs": {}},
        {"args": ["###"], "kwargs": {}},
        {"args": ["#9lives and #9Lives"], "kwargs": {}},
        {"args": ["start #Middle end"], "kwargs": {}},
    ],
})

TASKS.append({
    "id": "t30_char_frequency",
    "function": "char_frequency",
    "title": "Letter frequency of a string",
    "category": "string",
    "return_type": "dict",
    "signature": "char_frequency(text: str) -> dict",
    "doc": "Count each ASCII letter of a string, case-insensitively.",
    "description": """\
Count how often each letter occurs in `text`.

- Consider only ASCII letters `A-Z` and `a-z`. Digits, spaces, punctuation and
  any other character are ignored completely.
- Counting is case-insensitive and the keys are the **lowercase** letters, so
  `"AaBb"` gives `{"a": 2, "b": 2}`.
- A letter that does not occur has no key at all; do not include zero counts.
- The values are `int` counts.
- Key order does not matter.
- Text with no letters (including the empty string) returns an empty dictionary
  `{}`.""",
    "body": """\
    counts = {}
    for ch in text.lower():
        if "a" <= ch <= "z":
            counts[ch] = counts.get(ch, 0) + 1
    return counts""",
    "visible": [
        {"args": ["hello"], "kwargs": {}},
        {"args": [""], "kwargs": {}},
        {"args": ["AaBb"], "kwargs": {}},
    ],
    "hidden": [
        {"args": ["abc"], "kwargs": {}},
        {"args": ["aaa"], "kwargs": {}},
        {"args": ["Hello, World!"], "kwargs": {}},
        {"args": ["123 456"], "kwargs": {}},
        {"args": ["The quick brown fox"], "kwargs": {}},
        {"args": ["zzz ZZZ"], "kwargs": {}},
        {"args": ["x"], "kwargs": {}},
        {"args": ["  "], "kwargs": {}},
        {"args": ["Mississippi"], "kwargs": {}},
        {"args": ["AEIOU aeiou"], "kwargs": {}},
    ],
    "probes": [
        {"args": ["banana"], "kwargs": {}},
        {"args": ["Coffee"], "kwargs": {}},
        {"args": ["9876"], "kwargs": {}},
        {"args": ["Programming"], "kwargs": {}},
        {"args": ["q"], "kwargs": {}},
        {"args": ["TITLE Case"], "kwargs": {}},
        {"args": ["!!!"], "kwargs": {}},
        {"args": ["Zebra stripes"], "kwargs": {}},
        {"args": ["aAbBcC"], "kwargs": {}},
    ],
})
