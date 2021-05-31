r"""Provides tools to parse and convert PEG grammars and expressions

Much of the syntax is pretty intuitive. `|` is for ordered choice, ` ` to
join expressions, `!` for negative lookahead, `&` for positive lookahead, `*`
for zero or more matches, `+` for one or more matches, `?` for an optional
match, `.` for any character, and brackets `()` for grouping.

There are some differences however. A double quoted string means all characters
must match in order, whereas a single quoted string means one of the characters
are to be matched.

There are a few extra operations to help improve the parse tree. A backticked
string inserts the string in the result. Curly brackets around an expression
wraps the result in a tuple. A `~` prefix fuses the result into a single
string. A `:` prefix ignores the result.

    >>> rule = create_rule("'ab'+")
    >>> rule
    OneOrMore(ExpectChoice('ab'))
    >>> print(rule)
    'ab'+

    >>> grammar = create_grammar("ab <- 'ab'+;")
    >>> grammar
    Grammar(rules={'ab': OneOrMore(ExpectChoice('ab'))}, start='ab')
    >>> print(grammar)
    ab <- 'ab'+;

Here is the grammar that this module uses to parse strings. Start rules are
grammar_start and expression_start for grammars and expressions respectively.

    grammar_start <- _ grammar _ !.
    grammar <- { `grammar` definition (_ definition)* }
    definition <- { `definition` name _ :"<-" _ expression (_ :";")? }
    expression_start <- _ expression _ !.
    expression <- { `choices` joined (_ :"|" _ joined)+ } | joined
    joined <- { `joined` prefixed (_ prefixed)+ } | prefixed
    prefixed <- error | { `prefixed` (':~&!' _)+ repeated } | repeated
    repeated <- { `repeated` atom (_ '*+?')+ } | atom
    atom <- expectany | expectall | inject | dot | reference | curly | round
    curly <- { `packed` :"{" _ (expression | { `empty` () }) _ :"}" }
    round <- :"(" _ (expression | { `empty` () }) _ :")"
    error <- { `error` :"^" _ (sstring | dstring) }
    expectany <- { `expectany` sstring }
    expectall <- { `expectall` dstring }
    inject <- { `inject` bstring }
    dot <- { `dot` "." }
    reference <- { `reference` name !(_ "<-") }
    sstring <- ~("'" ("\\" . | !"'" .)+ "'")
    dstring <- ~("\"" ("\\" . | !"\"" .)+ "\"")
    bstring <- ~("`" ("\\" . | !"`" .)+ "`")
    name <- ~'_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'+
    _ <- :(' \t\n' | "#" (!("\n" | !.) .)* "\n"?)*

"""
from ast import literal_eval

from .grammar import Grammar
from .rule import *

__all__ = ["create_rule", "create_grammar"]

# This holds the rules to parse PEG grammars. Note that this grammar has no
# error messages.
grammar = Grammar(rules={
    "grammar_start": Join(
        Reference("_"),
        Reference("grammar"),
        Reference("_"),
        Negative(Any()),
    ),

    "grammar": Pack(Join(Inject("grammar"),
        Reference("definition"),
        Repeat(Join(
            Reference("_"),
            Reference("definition"),
        )),
    )),

    "definition": Pack(Join(Inject("definition"),
        Reference("name"),
        Reference("_"),
        Ignore(ExpectJoin("<-")),
        Reference("_"),
        Reference("expression"),
        Optional(Join(
            Reference("_"),
            Ignore(Expect(";")),
        )),
    )),

    "expression_start": Join(
        Reference("_"),
        Reference("expression"),
        Reference("_"),
        Negative(Any()),
    ),

    "expression": Choice(
        Pack(Join(Inject("choices"),
            Reference("joined"),
            OneOrMore(Join(
                Reference("_"),
                Ignore(Expect("|")),
                Reference("_"),
                Reference("joined"),
            )),
        )),
        Reference("joined"),
    ),

    "joined": Choice(
        Pack(Join(Inject("joined"),
            Reference("prefixed"),
            OneOrMore(Join(
                Reference("_"),
                Reference("prefixed"),
            )),
        )),
        Reference("prefixed"),
    ),

    "prefixed": Choice(
        Reference("error"),
        Pack(Join(Inject("prefixed"),
            OneOrMore(Join(
                ExpectChoice(":~&!"),
                Reference("_"),
            )),
            Reference("repeated"),
        )),
        Reference("repeated"),
    ),

    "repeated": Choice(
        Pack(Join(Inject("repeated"),
            Reference("atom"),
            OneOrMore(Join(
                Reference("_"),
                ExpectChoice("*+?"),
            )),
        )),
        Reference("atom"),
    ),

    "atom": Choice(
        Reference("expectany"),
        Reference("expectall"),
        Reference("inject"),
        Reference("dot"),
        Reference("reference"),
        Reference("curly"),
        Reference("round"),
    ),

    "curly": Pack(Join(Inject("packed"),
        Ignore(Expect("{")),
        Reference("_"),
        Choice(
            Reference("expression"),
            Pack(Join(Inject("empty"), Empty())),
        ),
        Reference("_"),
        Ignore(Expect("}")),
    )),

    "round": Join(
        Ignore(Expect("(")),
        Reference("_"),
        Choice(
            Reference("expression"),
            Pack(Join(Inject("empty"), Empty())),
        ),
        Reference("_"),
        Ignore(Expect(")")),
    ),

    "error": Pack(Join(Inject("error"),
        Ignore(Expect("^")),
        Reference("_"),
        Choice(
            Reference("sstring"),
            Reference("dstring"),
        ),
    )),

    "expectany": Pack(Join(Inject("expectany"), Reference("sstring"))),
    "expectall": Pack(Join(Inject("expectall"), Reference("dstring"))),
    "inject": Pack(Join(Inject("inject"), Reference("bstring"))),
    "dot": Pack(Join(Inject("dot"), Expect("."))),

    "reference": Pack(Join(Inject("reference"),
        Reference("name"),
        Negative(Join(
            Reference("_"),
            ExpectJoin("<-"),
        )),
    )),

    "sstring": Fuse(Join(
        Expect("'"),
        OneOrMore(Choice(
            Join(Expect("\\"), Any()),
            Join(Negative(Expect("'")), Any()),
        )),
        Expect("'"),
    )),
    "dstring": Fuse(Join(
        Expect('"'),
        OneOrMore(Choice(
            Join(Expect("\\"), Any()),
            Join(Negative(Expect('"')), Any()),
        )),
        Expect('"'),
    )),
    "bstring": Fuse(Join(
        Expect("`"),
        OneOrMore(Choice(
            Join(Expect("\\"), Any()),
            Join(Negative(Expect("`")), Any()),
        )),
        Expect("`"),
    )),

    "name": Fuse(OneOrMore(ExpectChoice(
        "_abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ))),

    "_": Ignore(Repeat(Choice(
        ExpectChoice(" \t\n"),
        Join(
            Expect("#"),
            Repeat(Join(
                Negative(Choice(
                    Expect("\n"),
                    Negative(Any()),
                )),
                Any(),
            )),
            Optional(Expect("\n")),
        ),
    ))),
})

def walk(node):
    """Recursively converts each tuple into a rule"""
    type_, *rest = node
    if type_ == "empty":
        return Empty()
    if type_ == "expectany":
        string = literal_eval(rest[0])
        return ExpectChoice(string)
    if type_ == "expectall":
        string = literal_eval(rest[0])
        return ExpectJoin(string)
    if type_ == "inject":
        string = literal_eval('"' + rest[0][1:-1].replace('"', '\\"') + '"')
        return Inject(string)
    if type_ == "dot":
        return Any()
    if type_ == "reference":
        name = rest[0]
        return Reference(name)
    if type_ == "packed":
        return Pack(walk(rest[0]))
    if type_ == "error":
        string = literal_eval(rest[0])
        return Error(string)
    if type_ == "repeated":
        rule = walk(rest[0])
        for repeat in rest[1:]:
            if repeat == "*":
                rule = ZeroOrMore(rule)
                continue
            if repeat == "+":
                rule = OneOrMore(rule)
                continue
            if repeat == "?":
                rule = Optional(rule)
                continue
            raise ValueError(f"unknown repeat: {repeat!r}")
        return rule
    if type_ == "prefixed":
        rule = walk(rest[-1])
        for prefix in reversed(rest[:-1]):
            if prefix == ":":
                rule = Ignore(rule)
                continue
            if prefix == "~":
                rule = Fuse(rule)
                continue
            if prefix == "!":
                rule = Negative(rule)
                continue
            if prefix == "&":
                rule = Positive(rule)
                continue
            raise ValueError(f"unknown prefix: {prefix!r}")
        return rule
    if type_ == "joined":
        return Join(*map(walk, rest))
    if type_ == "choices":
        return Choice(*map(walk, rest))
    if type_ == "definition":
        return (rest[0], walk(rest[1]))
    if type_ == "grammar":
        grammar = Grammar()
        for definition in rest:
            name, rule = walk(definition)
            if grammar.start is None:
                grammar.start = name
            grammar.rules[name] = rule
        return grammar
    raise ValueError(f"unknown node: {node!r}")

def create_rule(string):
    """Creates a rule from a string"""
    return walk(grammar.parse(string, start="expression_start")[0])

def create_grammar(string):
    """Creates a grammar from a string"""
    return walk(grammar.parse(string, start="grammar_start")[0])

def test_rule_str():
    for name, rule in grammar.rules.items():
        assert str(create_rule(str(rule))) == str(rule)
    assert str(create_grammar(str(grammar))) == str(grammar)
