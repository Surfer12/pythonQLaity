# How to update the Python parser

## Step 1: Add an extractor test

Extractor parser tests live in the `tests/parser` directory. There are two different kinds of tests

- Tests that compare the behavior of the old (Python-based) and new (`tree-sitter`-based) parsers, and verify that they yield the same output on the given source files, and
- Tests that compare the output of the parser (old or new) against a fixed `.expected` file.

What kind of test is run is determined based on the file name.
If it ends in either `_new.py` or `_old.py`, then the test is run against an `.expected` file. If not, it is used to compare old against new.

In most cases when adding new features, you'll only be interested in modifying the new parser (the old one is mostly there for legacy reasons).
Thus, you will almost certainly want to create a test that ends in `_new.py`.

It's a good habit to start by adding the parser test, as this makes it more easy to test when various bits of the parser have been added/modified successfully.

The rest of this document will only concern itself with the process of extending the _new_ parser.

To actually _run_ the tests, the easiest way is to use `pytest`.
In the main `extractor` directory (i.e. where this file is located) run

```sh
pytest tests/test_parser.py
```

and wait for the tests to complete. It is normal and expected that the test seemingly freezes on the first run.
This is simply because the `tsg-python` Rust binary is being built in the background.

Once you have added a new test (or modified an old one) and start making modifications to the parser itself, it quickly becomes tedious to run _all_ the parser tests.
To run just a single test using `pytest`, use the `::` syntax to specify specific tests.
For instance, if you want to just run the tests associated with the file `types_new.py`, you would write

```sh
pytest tests/test_parser.py::ParserTest::test_types_new
```

## Step 2: Extend the `tree-sitter-python` grammar

The new parser is based on `tree-sitter`, so the first task is to extend the existing `tree-sitter-python` grammar.
This grammar can be found in the `grammar.js` file in the `tsg-python/tsp` subdirectory of the extractor directory.

Note that whenever changes are made to `grammar.js`, you must regenerate the parser files by running

```sh
tree-sitter generate
```

inside the `tsp` directory.
You'll need to install the `tree-sitter` CLI in order to run this command.
One way to install it is to use `cargo`:

```sh
cargo install tree-sitter-cli
```

(This presupposes you have `cargo` available, but you'll need this anyway when compiling `tsg-python`.)

Once the parser files have been regenerated, they'll get picked up automatically when `tsg-python` is rebuilt.

> Pro-tip: When you're done with your parser changes, and go to commit these to a branch, put the autogenerated files in their own commit.
> This makes it easier to review the changes, and if you need to go back and regenerate the files again, it's easy to modify just that commit.

Once you have extended `grammar.js` and regenerated the parser files, you should be able to check that the grammar changes are sufficient by rerunning the parser test using `pytest`. If it fails while producing an AST that doesn't make sense, then you're probably on the right track. If it fails _without_ producing an AST, then something went wrong with the actual `tree-sitter` parse. To check if this is the case, you can run

```sh
tree-sitter parse path/to/test.py
```

and see what kind of errors are emitted (possibly as `ERROR` or `MISSING` nodes in the AST that is output).

## Step 3: Extend `python.tsg`

Once the grammar has been extended, we need to also tell `tsg-python` how to turn the `tree-sitter-python` AST into something that better matches the AST structure that we use in the Python extractor.

For an introduction to the language of `tree-sitter-graph` (and in particular how we use it in the Python extractor), see the `README.md` file in the `tsg-python` directory.

## Step 4: Extend the set of known AST nodes

If you added new node types, or added fields to known node types, then you'll need to update a few files in the Python extractor before it is able to reconstruct the output from `tsg-python`.

New AST nodes should be added in two places: `master.py` and `semmle/python/ast.py`. The former of these is used to automatically generate the Python dbscheme and `AstGenerated.qll`. The latter is what the parser actually uses as its internal representation of the AST.

## Step 5: Rebuild the autogenerated AST and database scheme

If you made changes to `master.py`, you'll need to regenerate a couple of files. This can be done from within the `extractor` directory using the `make dbscheme` and `make ast` commands. Note that for the latter, you need a copy of the CodeQL CLI present, as it is used to autoformat the `AstGenerated.qll` file.

## Step 6: Add dbscheme upgrade and downgrade scripts

If you ended up making changes to the database scheme inw step 5, then you'll need to add an appropriate pair of up- and downgrade scripts to handle any changes between the different versions of the dbscheme.

This can be a bit fiddly, but luckily there are [tools](https://github.com/github/codeql/blob/main/misc/scripts/prepare-db-upgrade.sh) that can help set up some of the necessary files for you.

See also the [guide](https://github.com/github/codeql/blob/main/docs/prepare-db-upgrade.md) for preparing database upgrades.