from Errors import InvalidSyntaxError
from Constants import *
from Results import ParseResult
from Nodes import *


# ------------PARSER----------------


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.advance()

    def advance(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_token = self.tokens[self.token_idx]
        return self.current_token

    # -------------------#

    def parse(self):
        res = self.expr()
        if not res.error and self.current_token.type != TT_EOF:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "अपेक्षित(Expected) '+','-', '*' or  '/'",
                )
            )
        return res

    def expr(self):
        res = ParseResult()
        if self.current_token.matches(TT_KEYWORD, ("var", "चल")):
            res.register_advancement()
            self.advance()
            if self.current_token.type != "IDENTIFIER":
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "अपेक्षित चल शब्द (Expected Identifier)",
                    )
                )
            var_name = self.current_token
            res.register_advancement()
            self.advance()

            if self.current_token.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "अपेक्षित = (Expected =)",
                    )
                )
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))

        pass_keywords = (
            (TT_KEYWORD, "AND"),
            (TT_KEYWORD, "आणि"),
            (TT_KEYWORD, "OR"),
            (TT_KEYWORD, "किंवा"),
        )
        node = res.register(self.bin_op(self.comp_expr, pass_keywords))

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected 'VAR', int, float, identifier,'IF', 'FOR', 'WHILE', 'FUN', '+', '-' or '('",
                )
            )
        return res.success(node)

    def comp_expr(self):
        res = ParseResult()

        if self.current_token.matches(TT_KEYWORD, ("NOT", "नाही")):
            op_token = self.current_token
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_token, node))

        node = res.register(
            self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE))
        )

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected int, float, identifier, '+', '-', '(' or 'NOT'",
                )
            )

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.power, (TT_MUL, TT_DIV))

    def factor(self):
        res = ParseResult()
        token = self.current_token
        if token.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(token, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (TT_POWER,), self.factor)

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res

        if self.current_token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_token.pos_start,
                            self.current_token.pos_end,
                            "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'",
                        )
                    )

                while self.current_token.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res

                if self.current_token.type != TT_RPAREN:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_token.pos_start,
                            self.current_token.pos_end,
                            f"Expected ',' or ')'",
                        )
                    )

                res.register_advancement()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def atom(self):
        res = ParseResult()
        token = self.current_token
        if self.current_token.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(token))

        if self.current_token.type in (TT_STRING):
            res.register_advancement()
            self.advance()
            return res.success(StringNode(token))

        if self.current_token.type in (TT_IDENTIFIER):
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(token))

        if token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        "अपेक्षित(Expected) ')' ",
                    )
                )

        if token.matches(TT_KEYWORD, ("IF", "जर")):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)
        if token.matches(TT_KEYWORD, ("FOR", "वारंवार")):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)

        if token.matches(TT_KEYWORD, ("WHILE", "जोपर्यंत")):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)

        if token.matches(TT_KEYWORD, ("FUN", "कार्य")):
            func_def = res.register(self.func_def())
            if res.error:
                return res
            return res.success(func_def)

        return res.failure(
            InvalidSyntaxError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "अपेक्षित(Expected) int,float, identifier,'IF', 'FOR', 'WHILE', 'FUN', '+','-' or  '('",
            )
        )

    def if_expr(self):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TT_KEYWORD, ("IF", "जर")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'IF'",
                )
            )

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        if not self.current_token.matches(TT_KEYWORD, ("THEN", "तर")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'तर' ('THEN')",
                )
            )

        res.register_advancement()
        self.advance()

        expr = res.register(self.expr())
        if res.error:
            return res
        cases.append((condition, expr))

        while self.current_token.matches(TT_KEYWORD, ("ELIF", "किंवाजर")):
            res.register_advancement()
            self.advance()

            condition = res.register(self.expr())
            if res.error:
                return res

            if not self.current_token.matches(TT_KEYWORD, ("THEN", "तर")):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        f"Expected 'तर' ('THEN') ",
                    )
                )

            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res
            cases.append((condition, expr))

        if self.current_token.matches(TT_KEYWORD, ("ELSE", "नाहीतर")):
            res.register_advancement()
            self.advance()

            else_case = res.register(self.expr())
            if res.error:
                return res

        return res.success(IfNode(cases, else_case))

    def for_expr(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, ("FOR", "वारंवार")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_tok.pos_end,
                    f"Expected 'FOR'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_tok.pos_end,
                    f"Expected identifier",
                )
            )

        var_name = self.current_token
        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_EQ:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected '='",
                )
            )

        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error:
            return res

        if not self.current_token.matches(TT_KEYWORD, ("TO", "ते")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'TO'",
                )
            )

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error:
            return res

        if self.current_token.matches(TT_KEYWORD, ("STEP", "पाऊल")):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error:
                return res
        else:
            step_value = None

        if not self.current_token.matches(TT_KEYWORD, ("THEN", "तर")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'THEN'",
                )
            )

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error:
            return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body))

    def while_expr(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, ("WHILE", "जोपर्यंत")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'WHILE'",
                )
            )

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        if not self.current_token.matches(TT_KEYWORD, ("THEN", "तर")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'THEN'",
                )
            )

        res.register_advancement()
        self.advance()

        body = res.register(self.expr())
        if res.error:
            return res

        return res.success(WhileNode(condition, body))

    def func_def(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, ("FUN", "कार्य")):
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected 'FUN'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_IDENTIFIER:
            var_name_token = self.current_token
            res.register_advancement()
            self.advance()
            if self.current_token.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        f"Expected '('",
                    )
                )
        else:
            var_name_token = None
            if self.current_token.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        f"Expected identifier or '('",
                    )
                )

        res.register_advancement()
        self.advance()
        arg_name_tokens = []

        if self.current_token.type == TT_IDENTIFIER:
            arg_name_tokens.append(self.current_token)
            res.register_advancement()
            self.advance()

            while self.current_token.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_token.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_token.pos_start,
                            self.current_token.pos_end,
                            f"Expected identifier",
                        )
                    )

                arg_name_tokens.append(self.current_token)
                res.register_advancement()
                self.advance()

            if self.current_token.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        f"Expected ',' or ')'",
                    )
                )
        else:
            if self.current_token.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start,
                        self.current_token.pos_end,
                        f"Expected identifier or ')'",
                    )
                )

        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_ARROW:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Expected '->'",
                )
            )

        res.register_advancement()
        self.advance()
        node_to_return = res.register(self.expr())
        if res.error:
            return res

        return res.success(FuncDefNode(var_name_token, arg_name_tokens, node_to_return))

    ################

    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        res = ParseResult()
        left = res.register(func_a())
        if res.error:
            return res

        while (
            self.current_token.type in ops
            or (self.current_token.type, self.current_token.value) in ops
        ):
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_token, right)
        return res.success(left)
