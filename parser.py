from functools import reduce

from combinators import Parser, constant, regex, ParseError
from nodes import *

whitespace = regex(r"[\s]+")
comments = regex("[/][/].*") | regex(r"[/][*].[\s\S]*[*][/]")
ignored = (whitespace | comments).repeat()
token = lambda pattern: (regex(pattern) & ignored).map(lambda x, _: x)
infix = lambda operator_parser, term_parser: term_parser.bind(lambda head:
    operator_parser.bind(lambda op: term_parser.map(lambda term: (op, term)))
    .repeat().map(lambda tail:
        reduce(lambda x, op_y: BinaryOperation(x, *op_y), tail, head)))

FUNCTION = token(r"function\b")
IF = token(r"if\b")
ELSE = token(r"else\b")
RETURN = token(r"return\b")
VAR = token(r"var\b")
WHILE = token(r"while\b")
COMMA = token("[,]")
SEMICOLON = token("[;]")
LEFT_PAREN = token("[(]")
RIGHT_PAREN = token("[)]")
LEFT_BRACE = token("[{]")
RIGHT_BRACE = token("[}]")

CHAR = token("'[^']'").map(lambda source: Number(ord(source[1])))
NUMBER = token("[0-9]+").map(lambda digits: Number(int(digits))) | CHAR
ID = token("[a-zA-Z_][a-zA-Z0-9_]*")

NOT = token("!").map(lambda _: Not)
ASSIGN = token("[=]").map(lambda _: Assign)
EQUAL = token("==").map(lambda _: "==")
NOT_EQUAL = token("!=").map(lambda _: "!=")
PLUS = token("[+]").map(lambda _: "+")
MINUS = token("[-]").map(lambda _: "-")
STAR = token("[*]").map(lambda _: "*")
SLASH = token("[/]").map(lambda _: "/")

# this is expression declaration, the definition will be later
expression = Parser()

# arguments <- (expression (COMMA expression)*)?
arguments = (expression & (COMMA & expression).repeat()).map(
    (lambda head, tail: [head] + [e for _, e in tail])
) | constant([])

# call <- ID LEFT_PAREN arguments RIGHT_PAREN
call = (ID & LEFT_PAREN & arguments & RIGHT_PAREN).map(
    lambda callee, left, arguments, right: Call(callee, arguments)
)

# atom <- call / ID / INTEGER / LEFT_PAREN expression RIGHT_PAREN
atom = ( call | ID.map(lambda name: Id(name)) | NUMBER
    | (LEFT_PAREN & expression & RIGHT_PAREN).map(lambda _, expr, __: expr)
)

# unary <- NOT ? atom
unary = (NOT.maybe() & atom).map(lambda n, t: Not(t) if n else t)

# infix operators
product = infix(STAR | SLASH, unary)
sum_expr = infix(PLUS | MINUS, product)
comparison = infix(EQUAL | NOT_EQUAL, sum_expr)

# expression <- comparison
expression.parse = comparison.parse


# this is statement declaration, the definition will be later
statement = Parser()

# return_stmt <- RETURN expression SEMICOLON
return_stmt = (RETURN & expression & SEMICOLON).map(
    lambda _return, e, _semicolon: Return(e)
)

# expression_stmt <- expression SEMICOLON
expression_stmt = (expression & SEMICOLON).map(lambda term, _: term)

# if_stmt <- IF LEFT_PAREN expression RIGHT_PAREN statement ELSE statement
if_stmt = (
    IF & LEFT_PAREN & expression & RIGHT_PAREN & statement & ELSE & statement
).map(lambda _if, _left, condition, _right, consequence, _else, alternative:
    If(condition, consequence, alternative)
)

# while_stmt <- WHILE LEFT_PAREN expression RIGHT_PAREN statement
while_stmt = (WHILE & LEFT_PAREN & expression & RIGHT_PAREN & statement).map(
    lambda _while, _left, condition, _right, body: While(condition, body)
)

# var_stmt <- VAR ID ASSIGN expression SEMICOLON
var_stmt = (VAR & ID & ASSIGN & expression & SEMICOLON).map(
    lambda _var, name, _assign, value, _semicolon: Var(name, value)
)

# assignment_stmt <- ID ASSIGN expression SEMICOLON
assignment_stmt = (ID & ASSIGN & expression & SEMICOLON).map(
    lambda name, _assign, value, _semicolon: Assign(name, value)
)

# block_stmt <- LEFT_BRACE statement* RIGHT_BRACE
block_stmt = (LEFT_BRACE & statement.repeat() & RIGHT_BRACE).map(
    lambda _left, stmts, _right: Block(stmts)
)

# parameters <- (ID (COMMA ID)*)?
parameters = (ID & (COMMA & ID).repeat()).map(
    lambda head, tail: [head] + [arg for _, arg in tail]
) | constant([])

# function_stmt <- FUNCTION ID LEFT_PAREN parameters RIGHT_PAREN block_stmt
function_stmt = (
    FUNCTION & ID & LEFT_PAREN & parameters & RIGHT_PAREN & block_stmt
).map(lambda _function, name, _left, params, _right, body:
    Function(name, params, body)
)

# statement <- all the statements defined above
statement.parse = (
    return_stmt | function_stmt | if_stmt | while_stmt
    | var_stmt | assignment_stmt | block_stmt | expression_stmt
).parse

# the parser of the whole language
parser = (ignored & statement.repeat()).map(lambda _, stmts: Block(stmts))
