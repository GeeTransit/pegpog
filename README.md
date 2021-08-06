# pegpog

A simple PEG parser

## Quickstart

Run `python quicktest.py`, put the following in the Grammar textbox, put a
simple math expression in the Input textbox, and hit the Parse button.

    start <- _ expression _ !.;
    expression <- { `expression` factor (_ '+-' _ factor)+ } | factor;
    factor <- { `factor` term (_ '*/' _ term)+ } | term;
    term <- :"(" _ expression _ ":)" | { `num` ~'0123456789'+ };
    _ <- :" "*;

## Tutorial

Let's create a simple calculator. We'll try to parse `"6 + 9*42 - (0)"`.
Here are the rules that we would start with:

    expression <- factor ('+-' factor)+ | factor;
    factor <- term ('*/' term)+ | term;
    term <- "(" expression ")" | '0123456789'+;

If we create a grammar out of this and try to parse our expression, it returns
(6,). What? The reason it's doing this is because it could only parse up to 6
without failing. We want it to parse the whole input, so let's add a start rule
that ends in `!.`. This rule only succeeds at the end of the string, so we can
use it to force the rule to parse until the end or fail otherwise.

    start <- expression !.;

Aw, we still get an error. the `.` in our `start` rule still succeeds, which
makes the `!.` fail, thus failing the whole rule. However, if we remove all
spaces from the expression, we get `"6+9*42-(0)"`, and this succeeds. It was
failing before because there were spaces in the input, so let's add spaces
where necessary. I like to put them in a rule named `_` so it doesn't stand out
in the rules where it's used.

    start <- _ expression _ !.;
    expression <- factor (_ '+-' _ factor)+ | factor;
    factor <- term (_ '*/' _ term)+ | term;
    term <- "(" _ expression _ ")" | '0123456789'+;
    _ <- " "*;

Now it can parse the original input! However, the result is pretty useless.

    ('6', ' ', '+', ' ', '9', '*', '4', '2', ' ', '-', ' ', '(', '0', ')')

This is the same as `tuple("6 + 9*42 - (0)")`. Let's first start by ignoring
the spaces. We'll prefix a `:` on the `_` rule to ignore whatever `" "*` gave.

    _ <- :" "*;

This gives us

    ('6', '+', '9', '*', '4', '2', '-', '(', '0', ')')

Better than before, but still pretty useless. It's the same as
`tuple("6 + 9*42 - (0)".replace(" ", ""))`. Our next move is to give our result
some depth. Let's add some `{}` around some operations and see what it does.

    start <- _ expression _ !.;
    expression <- { factor (_ '+-' _ factor)+ } | factor;
    factor <- { term (_ '*/' _ term)+ } | term;
    term <- { "(" _ expression _ ")" } | '0123456789'+;
    _ <- :" "*;

Nice. Now we have some more useful output. I'll format it for readability.

    ( ( '6',
        '+',
        ( '9',
          '*',
          '4', '2'),
        '-',
        ( '(',
          '0',
          ')')),)

Still kinda cluttered. How about now?

    '6'
    '+'
        '9'
        '*'
        '4', '2'
    '-'
        '('
        '0'
        ')'

Pretty neat. Our parser already knows the order of operations as shown by the
`9*42` being indented together, rather than say `6+9` being together. This is
due to expression being defined as factors separated by `+` or `-` and factors
defined as terms separated by `*` or `/`. The factor would be parsed together,
then the expression would connect them a level up.

It's possible to create a function that walks through this and evaluates the
answer, though it requires quite a bit of effort.

One way to make it simpler for the walker is to use the `~` prefix which joins
the expression into a single string. The `42` is current represented as
`('4', '2')` which makes finding where the number ends harder than necessary.
Let's prefix our rule for a number with the fuse operator.

    term <- { "(" _ expression _ ")" } | ~'0123456789'+;

Now when we parse, the `42` is in a single string.

    '6'
    '+'
        '9'
        '*'
        '42'
    '-'
        '('
        '0'
        ')'

How about we also remove the brackets? They were only there to "override"
operator precedence so that it would act on the expression inside as a single
number. They have no use in the final parse tree, so let's prefix them with a
`:`, same as what we did to spaces. For the same reason, we can also remove the
curly brackets.

    term <- :"(" _ expression _ :")" | ~'0123456789'+;

Now we have an even cleaner tree.

    '6'
    '+'
        '9'
        '*'
        '42'
    '-'
    '0'

Here is my walker function for this step as reference. Note that you need to
pass in the first item inside the result because the expression rule packs the
result inside a tuple.

    def walk(node):
        if isinstance(node, str):
            return int(node)
        node = list(node)
        value = walk(node.pop(0))
        while node:
            op = node.pop(0)
            other = walk(node.pop(0))
            if op == "+":
                value += other
            elif op == "-":
                value -= other
            elif op == "*":
                value *= other
            elif op == "/":
                value /= other
        return value

The answer's 384 by the way. Anyways, this walker function works, but
improvements can be made. Instead of an `isinstance` check, we can pack it in
another tuple and use the inject syntax to our advantage. Take a look:

    term <- :"(" _ expression _ :")" | { `num` ~'0123456789'+ };

When we parse our expression, all numbers are now actually a two-tuple of the
form `('num', string)`.

    'num', '6'
    '+'
        'num', '9'
        '*'
        'num', '42'
    '-'
    'num', '0'

Our walker function can now check whether the first item is `num` and act
accordingly.

    if node[0] == "num":
        return int(node[1])

We can extend this to our expressions and factors too. Instead of checking the
operator, we can have the first item be either `expression` or `factor` and
then act on them separately.

    expression <- { `expression` factor (_ '+-' _ factor)+ } | factor;
    factor <- { `factor` term (_ '*/' _ term)+ } | term;

Our walker function can now look like this:

    if node[0] == "expression":
        node = list(node[1:])
        value = walk(node.pop(0))
        while node:
            op = node.pop(0)
            other = walk(node.pop(0))
            if op == "+":
                value += other
            elif op == "-":
                value -= other
        return value
    if node[0] == "factor":
        node = list(node[1:])
        value = walk(node.pop(0))
        while node:
            op = node.pop(0)
            other = walk(node.pop(0))
            if op == "*":
                value *= other
            elif op == "/":
                value /= other
        return value

This creates a parallel between the parsing and the walking and ensures that
the operators inside each type of rule are actually the correct ones.

    'expression'
        'num', '6'
        '+'
        'factor'
            'num', '9'
            '*'
            'num', '42'
        '-'
        'num', '0'

Here's the result with all syntax `(,)` for reference:

    (('expression',
        ('num', '6'),
        '+',
        ('factor',
            ('num', '9'),
            '*',
            ('num', '42')),
        '-',
        ('num', '0')),)

One can turn the walker function into a class that uses getattr to act on
different nodes but I'm content with the walker being a function.

