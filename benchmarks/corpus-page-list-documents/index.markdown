Pagination Benchmark
====================

This benchmark was made to explicit the gain in response time of
[pypln.api](https://github.com/NAMD/pypln.api)'s `add_document` call when using
pagination on corpus page (document list).


Method
------

[pypln.api](https://github.com/NAMD/pypln.api) was used to add 1000 documents
in the same corpus. The tests were made in two versions of the code:

- [Without pagination](https://github.com/NAMD/pypln.web/commit/d4f942036f1472a26ac5bbeb823cc8dc7bf51fbd); and
- [With pagination](https://github.com/NAMD/pypln.web/commit/452566986c16e9fe10f4519753745c593244b7fc).


Running
-------

To run this benchmark, you first need to:

- Run [pypln.backend](https://github.com/NAMD/pypln.backend);
- Install [pypln.api](https://github.com/NAMD/pypln.api) (`pip install
  pypln.api` will do).

Then:

### Running first test (old code)

- Checkout to [pypln.web](https://github.com/NAMD/pypln.web)'s version [without
  pagination](https://github.com/NAMD/pypln.web/commit/d4f942036f1472a26ac5bbeb823cc8dc7bf51fbd)
  and run it (`python manage.py runserver`);
- Run `python benchmark.py old` (will take ~7 hours for 1k documents).

> Note that you can change the number of documents sent just changing the value
> of variable `number_of_documents` inside `benchmark.py`.

### Running second test (new code)

- Checkout to [pypln.web](https://github.com/NAMD/pypln.web)'s version [with
  pagination](https://github.com/NAMD/pypln.web/commit/452566986c16e9fe10f4519753745c593244b7fc)
  and run it (`python manage.py runserver`);
- Run `python benchmark.py new` (will take  ~40 minutes for 1k documents).

### Plotting the result

You need to have [gnuplot](http://gnuplot.info/) installed. Just run:

    gnuplot plot-time.gnu

And then `time.png` will be created.


Results
-------

The graph below shows duration of each request (request number versus execution
time of `corpus.add_document` method). All documents have almost the same size.

The old version (without pagination) increases upload time of each document
linearly since `pypln.api` needs to open corpus page (with its document list)
before doing the POST request to add the document.

![time](https://f.cloud.github.com/assets/186126/213161/c228cf96-8360-11e2-876b-6b2bb0cfafdb.png)

> Note: the peak in blue curve near 900th document were just I using other
> CPU-bound programs in my notebook ;) - sorry.
