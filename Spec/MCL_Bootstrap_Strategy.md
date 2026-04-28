# MCL Implementation Strategy: Bootstrap & Execution Plan

## The Bootstrap Problem

You could write the MCL compiler in C (the "right" language for compilers) or Python (faster to iterate). 

**DeepSeek's suggestion:** Write in Python first. Once it works, rewrite in MCL itself (self-hosting). This validates the entire language design.

This document outlines that two-phase approach.

---

## Phase 0: Bootstrap (Weeks 1-2)

### Why Bootstrap First?

A compiler written in MCL is the ultimate test of the language. It will expose:
- Missing operators or keywords
- Type system gaps
- Memory model problems (implicit allocations you missed)
- Performance bottlenecks

**Goal:** Build a working MCL compiler in Python → compile to C → test on real kernels → rewrite compiler in MCL.

---

## Week 1: Lexer & Parser (Python)

### Day 1-2: Lexer

**Goal:** Tokenize any MCL source file.

```python
# mcl_lexer.py

class Token:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
    
    def tokenize(self):
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            
            # Try to match operator, keyword, identifier, literal
            if self.match_operator():
                continue
            elif self.match_keyword_or_identifier():
                continue
            elif self.match_number():
                continue
            elif self.match_string():
                continue
            else:
                self.error(f"Unexpected character: {self.current_char()}")
        
        self.tokens.append(Token('EOF', None, self.line, self.col))
        return self.tokens
    
    # ... implement match_operator(), match_keyword_or_identifier(), etc.
```

**Lexer must recognize:**

**Operators (16 total):**
```
** * / + - < > = ≠ ≤ ≥ .AND. .OR. .NOT. :=
```

**Keywords:**
```
IF THEN ELSE ENDIF DO ENDDO
FUNCTION SUBROUTINE END RETURN
REAL INTEGER LOGICAL CHARACTER COMPLEX
ALLOCATABLE ALLOCATABLE DIMENSION
IMPLICIT NONE
CALL ALLOCATE DEALLOCATE
```

**Literals:**
```
Integers: 42, -5, 0
Reals: 3.14, -2.5, 1.0e-10
Strings: "hello", 'world'
Logical: .TRUE., .FALSE.
```

**Comments:**
```
! This is a comment to end of line
```

**Output:** List of `(TokenType, value, line, col)` tuples.

---

### Day 2-3: Parser (Recursive Descent)

**Goal:** Convert token stream → AST.

```python
# mcl_parser.py

class ASTNode:
    pass

class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name

class Literal(ASTNode):
    def __init__(self, type, value):
        self.type = type  # 'INTEGER', 'REAL', 'STRING', 'LOGICAL'
        self.value = value

class FunctionCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ArraySubscript(ASTNode):
    def __init__(self, array, indices):
        self.array = array
        self.indices = indices

class AssignmentStatement(ASTNode):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class IfStatement(ASTNode):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class DoLoop(ASTNode):
    def __init__(self, var, start, end, step, body):
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        statements = []
        while not self.is_at_end():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements
    
    def parse_statement(self):
        if self.match('IF'):
            return self.parse_if_statement()
        elif self.match('DO'):
            return self.parse_do_loop()
        elif self.match('ALLOCATE'):
            return self.parse_allocate()
        elif self.match('DEALLOCATE'):
            return self.parse_deallocate()
        elif self.match('FUNCTION'):
            return self.parse_function()
        elif self.match('SUBROUTINE'):
            return self.parse_subroutine()
        else:
            # Assignment or expression statement
            expr = self.parse_expression()
            self.consume('SEMICOLON', "Expected ';' after statement")
            return expr  # or wrap in ExpressionStatement if needed
    
    def parse_expression(self):
        return self.parse_or_expression()
    
    def parse_or_expression(self):
        left = self.parse_and_expression()
        while self.match('.OR.'):
            op = self.previous()
            right = self.parse_and_expression()
            left = BinaryOp(op, left, right)
        return left
    
    def parse_and_expression(self):
        left = self.parse_relational_expression()
        while self.match('.AND.'):
            op = self.previous()
            right = self.parse_relational_expression()
            left = BinaryOp(op, left, right)
        return left
    
    def parse_relational_expression(self):
        left = self.parse_additive_expression()
        
        # Check for comparison chain
        comparisons = []
        while self.match_relational_op():
            op = self.previous()
            right = self.parse_additive_expression()
            comparisons.append((left, op, right))
            left = right
        
        # Desugar chain: a < b ≤ c → (a < b) AND (b ≤ c)
        if len(comparisons) > 1:
            result = BinaryOp(comparisons[0][1], comparisons[0][0], comparisons[0][2])
            for i in range(1, len(comparisons)):
                right = BinaryOp(comparisons[i][1], comparisons[i][0], comparisons[i][2])
                result = BinaryOp('.AND.', result, right)
            return result
        elif len(comparisons) == 1:
            return BinaryOp(comparisons[0][1], comparisons[0][0], comparisons[0][2])
        else:
            return left
    
    def parse_additive_expression(self):
        left = self.parse_multiplicative_expression()
        while self.match('+', '-'):
            op = self.previous()
            right = self.parse_multiplicative_expression()
            left = BinaryOp(op, left, right)
        return left
    
    def parse_multiplicative_expression(self):
        left = self.parse_exponentiation_expression()
        while self.match('*', '/'):
            op = self.previous()
            right = self.parse_exponentiation_expression()
            left = BinaryOp(op, left, right)
        return left
    
    def parse_exponentiation_expression(self):
        left = self.parse_unary_expression()
        if self.match('**'):
            op = self.previous()
            right = self.parse_exponentiation_expression()  # Right-associative
            return BinaryOp(op, left, right)
        return left
    
    def parse_unary_expression(self):
        if self.match('+', '-', '.NOT.'):
            op = self.previous()
            operand = self.parse_unary_expression()  # Right-associative
            return UnaryOp(op, operand)
        return self.parse_postfix_expression()
    
    def parse_postfix_expression(self):
        expr = self.parse_primary()
        
        while True:
            if self.match('('):
                # Function call or array subscript
                args = self.parse_argument_list()
                self.consume(')', "Expected ')' after arguments")
                expr = FunctionCall(expr, args)
            else:
                break
        
        return expr
    
    def parse_primary(self):
        if self.match('INTEGER_LITERAL'):
            return Literal('INTEGER', self.previous().value)
        elif self.match('REAL_LITERAL'):
            return Literal('REAL', self.previous().value)
        elif self.match('STRING_LITERAL'):
            return Literal('STRING', self.previous().value)
        elif self.match('.TRUE.', '.FALSE.'):
            return Literal('LOGICAL', self.previous().value)
        elif self.match('IDENTIFIER'):
            return Variable(self.previous().value)
        elif self.match('('):
            expr = self.parse_expression()
            self.consume(')', "Expected ')' after expression")
            return expr
        else:
            self.error(f"Unexpected token: {self.current()}")
    
    # ... implement match(), consume(), error(), etc.
```

**Parser must:**
- Use **precedence climbing** for expressions
- **Desugar comparison chains** at parse time (1 < x ≤ 10 → (1 < x) AND (x ≤ 10))
- **Reject illegal patterns:**
  - Assignment chaining: `y := x := 5` (reject at parse time)
  - ALLOCATE as expression: `C := ALLOCATE(m, p)` (reject)
- Build proper AST for all statement types

---

### Day 3-4: Error Handling & AST Validation

**Goal:** Reject syntactically invalid MCL.

```python
def validate_ast(ast):
    """Reject illegal patterns"""
    for node in walk(ast):
        if isinstance(node, AssignmentStatement):
            # Check that target is not itself an assignment
            if isinstance(node.value, AssignmentStatement):
                error("Assignment chaining is illegal")
            
            # Check that RHS is not ALLOCATE(...)
            if isinstance(node.value, FunctionCall) and node.value.name == 'ALLOCATE':
                error("ALLOCATE cannot be used in expression context")
```

---

### Day 4-5: First Code Generation (C Backend, Skeletal)

**Goal:** Emit readable C code for valid MCL.

```python
# mcl_codegen_c.py

class CCodeGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.output = []
    
    def generate(self):
        self.output.append("#include <math.h>")
        self.output.append("#include <stdio.h>")
        self.output.append("typedef struct { int rank; int *dims; double *data; } Array;")
        
        # Generate function/subroutine code
        for node in self.ast:
            if isinstance(node, FunctionDef):
                self.generate_function(node)
        
        return "\n".join(self.output)
    
    def generate_function(self, func_node):
        self.output.append(f"double {func_node.name}(...) {{")
        
        for stmt in func_node.body:
            self.generate_statement(stmt)
        
        self.output.append("}")
    
    def generate_statement(self, stmt):
        if isinstance(stmt, AssignmentStatement):
            self.generate_assignment(stmt)
        elif isinstance(stmt, IfStatement):
            self.generate_if(stmt)
        elif isinstance(stmt, DoLoop):
            self.generate_do_loop(stmt)
    
    def generate_assignment(self, assign):
        target = self.generate_expression(assign.target)
        value = self.generate_expression(assign.value)
        self.output.append(f"{target} = {value};")
    
    def generate_expression(self, expr):
        if isinstance(expr, BinaryOp):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            op_map = {'+': '+', '-': '-', '*': '*', '/': '/', '**': 'pow', '<': '<', '>': '>', '=': '==', '.AND.': '&&', '.OR.': '||'}
            op = op_map[expr.op.value]
            if op == 'pow':
                return f"pow({left}, {right})"
            else:
                return f"({left} {op} {right})"
        elif isinstance(expr, Literal):
            return str(expr.value)
        # ... etc.
```

---

## End of Week 1 Target

✅ **Lexer** — Tokenizes all MCL source files  
✅ **Parser** — Builds AST from token stream, desugars comparison chains  
✅ **Validation** — Rejects assignment chaining, ALLOCATE in expressions  
✅ **C Codegen** — Generates readable C code (no optimization, but correct)  

**Test:** Compile a simple MCL kernel (N-body update loop, particle step, etc.) and verify generated C compiles and runs.

---

## Week 2: Type Checker & Semantic Analysis

### Phase 2 Deliverables

- [ ] Symbol table (track variable declarations, types, shapes)
- [ ] Type inference (infer types for expressions)
- [ ] Shape propagation (infer output shapes for MATMUL, TRANSPOSE, etc.)
- [ ] Allocation tracking (ensure allocatable arrays are allocated before use)
- [ ] Error checking (shape mismatches, type errors, etc.)

### Example: Shape Checking for MATMUL

```python
def check_matmul_shapes(self, a_shape, b_shape, c_shape):
    """Verify MATMUL shapes"""
    m, n = a_shape
    n2, p = b_shape
    
    if n != n2:
        error(f"MATMUL: inner dimension mismatch: {n} != {n2}")
    
    expected_shape = (m, p)
    if c_shape != expected_shape:
        error(f"MATMUL: output shape {c_shape} != expected {expected_shape}")
```

---

## Week 3-4: Optimization & Testing

- [ ] Inline simple intrinsics (SIN, COS, etc.)
- [ ] Optimize loops (loop unrolling, vectorization hints)
- [ ] Test on real kernels (Sanity hopfion update, N-body, etc.)

---

## After Python Bootstrap: Rewrite in MCL

Once the Python compiler works:

1. **Rewrite the lexer in MCL**
2. **Rewrite the parser in MCL**
3. **Rewrite the type checker in MCL**
4. **Rewrite the code generator in MCL**

This validates that MCL can express its own implementation. If you find gaps, fix the language design.

---

## Why Bootstrap in Python First?

| Aspect | Python | C | MCL |
|--------|--------|---|-----|
| Development speed | ⚡ Fast | 🐢 Slow | N/A (validates design) |
| Debugging | ✅ Easy | ⚠️ Medium | Forces design clarity |
| Dependencies | Simple | Few | None (but language still new) |
| Learning curve | ✅ Low | ⚠️ High | Medium (new language) |

**Decision:** Python for bootstrap (2 weeks) → works, then rewrite in MCL (2-3 weeks) to validate.

---

## Concrete Week 1 Milestones

| Day | Task | Output |
|-----|------|--------|
| Mon-Tue | Lexer | Tokenizes valid/invalid MCL, produces token stream |
| Wed | Parser scaffolding | Builds basic AST for expressions |
| Thu | Statement parsing | Handles IF, DO, FUNCTION, assignment |
| Fri | Codegen + testing | Generates C, compiles with gcc, runs |

---

## Test Cases for Week 1

```mcl
! test_arithmetic.ergo
REAL :: x, y, z
x := 5.0
y := 3.0
z := x + y * 2.0
PRINT z  ! Should be 11.0

! test_matmul.ergo
REAL :: A(2, 3), B(3, 2), C(2, 2)
! ... fill A and B ...
C := MATMUL(A, B)
PRINT C

! test_loop.ergo
DO i = 1, 10, 1
  PRINT i
ENDDO

! test_chaining.ergo
INTEGER :: x
x := 5
IF 0 < x ≤ 10:
  PRINT "x is in range"
ENDIF
```

---

## Success Criteria for Bootstrap

✅ All test cases compile and produce correct output  
✅ Generated C code is readable (can manually inspect for correctness)  
✅ No hidden allocations in generated code  
✅ Performance is reasonable (no N² behavior, loops inline as expected)  

Once bootstrap works, you have a **working MCL compiler**. Everything after that is optimization and self-hosting.

