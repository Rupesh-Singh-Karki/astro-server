# Let's Get Pythonic!

This is a set of guidelines for writing code in python the "pythonic" way or mode. Pythonic is a term used in Python that defines code that uses both the correct syntax and is clean, readable and easily maintained. Lets KISS!

Long Version - https://google.github.io/styleguide/pyguide.html (Best Guidelines on Internet!)

TLDR;

Short Version - 
## Variable Naming

Function names, variable names, and filenames should be descriptive; avoid abbreviation. In particular, do not use abbreviations that are ambiguous or unfamiliar to readers outside your project, and do not abbreviate by deleting letters within a word.

### Names to Avoid 
-   single character names, except for specifically allowed cases:
    
    -   counters or iterators (e.g.  `i`,  `j`,  `k`,  `v`, et al.)
    -   `e`  as an exception identifier in  `try/except`  statements.
    -   `f`  as a file handle in  `with`  statements
    -   private  [type variables](https://google.github.io/styleguide/pyguide.html#typing-type-var)  with no constraints (e.g.  `_T = TypeVar("_T")`,  `_P = ParamSpec("_P")`)
    
    Please be mindful not to abuse single-character naming. Generally speaking, descriptiveness should be proportional to the name’s scope of visibility. For example,  `i`  might be a fine name for 5-line code block but within multiple nested scopes, it is likely too vague.
    
-   dashes (`-`) in any package/module name
    
-   `__double_leading_and_trailing_underscore__`  names (reserved by Python)
    
-   offensive terms
    
-   names that needlessly include the type of the variable (for example:  `id_to_name_dict`)

### Naming Conventions

-   “Internal” means internal to a module, or protected or private within a class.
    
-   Prepending a single underscore (`_`) has some support for protecting module variables and functions (linters will flag protected member access). Note that it is okay for unit tests to access protected constants from the modules under test.
    
-   Prepending a double underscore (`__`  aka “dunder”) to an instance variable or method effectively makes the variable or method private to its class (using name mangling); we discourage its use as it impacts readability and testability, and isn’t  _really_  private. Prefer a single underscore.
    
-   Place related classes and top-level functions together in a module. Unlike Java, there is no need to limit yourself to one class per module.
    
-   Use CapWords for class names, but lower_with_under.py for module names. 
    
-   New  _unit test_  files follow PEP 8 compliant lower_with_under method names, for example,  `test_<method_under_test>_<state>`. For consistency(*) with legacy modules that follow CapWords function names, underscores may appear in method names starting with  `test`  to separate logical components of the name.

| Type | Public | Internal
| --- | --- | ---
Packages |	lower_with_under | 
Modules  |	lower_with_under	| _lower_with_under 
Classes	| CapWords |	_CapWords 
Exceptions | CapWords 
Functions |	lower_with_under() | _lower_with_under() 
Global/Class Constants |	CAPS_WITH_UNDER |	_CAPS_WITH_UNDER 
Global/Class Variables |	lower_with_under |	_lower_with_under 
Instance Variables |	lower_with_under|	_lower_with_under (protected) 
Method Names |	lower_with_under()	| _lower_with_under() (protected) 
Function/Method Parameters |	lower_with_under 
Local Variables	| lower_with_under

## Writing code and files

### One Statement of Code per Line

```python
#Bad

print 'foo'; print 'bar' 
if x == 1: print 'foo' 
if <complex comparison> and <other complex comparison>: # do something

#Good
print 'foo' 
print 'bar' 

if x == 1: 
  print 'foo' 

cond1 = <complex comparison> 
cond2 = <other complex comparison> 
if cond1 and cond2: 
    # do something
```

### Write Explicit Code

```python
#Bad
def make_complex(*args):
    x,y = args
    return dict(**locals())
    
#Good
def make_complex(x, y):  
    return { 'x' : x, 'y' : y}
```

### Return Statements

It is preferable to avoid returning meaningful values at multiple output points in the function body.

```python
#Bad

def complex_function(a, b, c):
  if not a:
    return None
  if not b:
    return None
  # Some complex code trying to compute x from a, b and c
  if x:
    return x
  if not x:  
    # Some Plan-B computation of x
    return x

#Good

def complex_function(a, b, c):
  if not a or not b or not c:
  raise ValueError("The args can't be None") 

  # Raising an exception is better

  # Some complex code trying to compute x from a, b and c
  # Resist temptation to return x if succeeded
  if not x:
  # Some Plan-B computation of x

  return x # One single exit point for the returned value x will help when maintaining the code.
```

### Unpacking of Variables

If you want to assign names or references to the elements of a list while unpacking it, try using enumerate():

```python

#Good 
for index, item in enumerate(some_list):
    # do something with index and item
```

You can use swap variables:

```python
#Good
a, b = b, a

a, (b, c) = 1, (2, 3)
```

Use the Python list * operator to create simple lists and nested lists as well:

```python
nones = [None]*4
foures_of_fours = [[4]]*5
```

### Access 

Don’t use the dict.has_key() method. Instead, use x in d syntax, or pass a default argument to dict.get(), as it is more Pythonic and is removed in Python 3.x.

```python
#Bad

d = {'foo': 'bar'}
if d.has_key('foo'):
    print d['foo']    # prints 'bar'
else:
    print 'default_value'

#Good

d = {'foo': 'bar'}

print d.get('foo', 'default_value') # prints 'bar'
print d.get('thingy', 'default_value') # prints 'default_value'

# alternative
if 'hello' in d:
    print d['foo']

```

### Filtering a List

Never remove items from a list while you are iterating it. Why? If your list is accessed via multiple references, the fact that you're just reseating one of the references (and NOT altering the list object itself) can lead to subtle, disastrous bugs.

```python
# Filter elements greater than 4
num_list = [1, 2, 3]
for i in num_list:
    if i > 2:
        num_list.remove(i)
```

Use a list comprehension or generator expression:

```python
# comprehensions create a new list object
filtered_values = [value for value in sequence if value != x]

# generators don't create another list
filtered_values = (value for value in sequence if value != x)
```

### Updating Values in a List

Remember that assignment never creates a new object. If two or more variables refer to the same list, changing one of them changes them all.

```python
#Bad

# Add three to all list members.
a = [3, 4, 5]
b = a                     # a and b refer to the same list object

for i in range(len(a)):
    a[i] += 3             # b[i] also changes

#Good
a = [3, 4, 5]
b = a

# assign the variable "a" to a new list without changing "b"
a = [i + 3 for i in a]
b = a[:]  # even better way to copy a list

```

### Read From a File

Use the with open syntax to read from files. This will automatically close files for you.

```python
#Bad

f = open('file.txt')
a = f.read()
print a
f.close()

#Good
with open('file.txt') as f:
    for line in f:
        print line

```

### Line Breaks

After annotating, many function signatures will become “one parameter per line”. To ensure the return type is also given its own line, a comma can be placed after the last parameter.

```python
#Bad
def my_method(self,
              other_arg: MyLongType | None,
             ) -> dict[OtherLongType, MyLongType]:

def my_method(self, other_arg: MyLongType | None) -> dict[OtherLongType, MyLongType]:

#Good

def my_method(
    self,
    other_arg: MyLongType | None,
) -> tuple[MyLongType1, MyLongType1]:
  ...
```

### Default Values

As per PEP-008, use spaces around the = only for arguments that have both a type annotation and a default value.

```python
#Bad
def func(a:int=0) -> int:
  ...

#Good
def func(a: int = 0) -> int:
  ...
```

### NoneType

In the Python type system, NoneType is a “first class” type, and for typing purposes, None is an alias for NoneType. If an argument can be None, it has to be declared! You can use | union type expressions (recommended in new Python 3.10+ code), or the older Optional and Union syntaxes. Use explicit X | None instead of implicit.

```python

#Not Recommended
def nullable_union(a: Union[None, str]) -> str:
  ...
def implicit_optional(a: str = None) -> str:
  ...

#Good
def modern_or_union(a: str | int | None, b: str | None = None) -> str:
  ...
def union_optional(a: Union[str, int, None], b: Optional[str] = None) -> str:
  ...

```

### Type Aliases

You can declare aliases of complex types. The name of an alias should be CapWorded. If the alias is used only in this module, it should be _Private.

```python
from typing import TypeAlias

_LossAndGradient: TypeAlias = tuple[tf.Tensor, tf.Tensor]
ComplexTFMap: TypeAlias = Mapping[str, _LossAndGradient]

```

### String Types

Use str for string/text data. For code that deals with binary data, use bytes.

```python
def deals_with_text_data(x: str) -> str:
  ...
def deals_with_binary_data(x: bytes) -> bytes:
  ...
```