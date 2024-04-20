<p align="center">
  <img src="/assets/marc.png">
</p>

# DMARC Reports viewer


## Installation

```shell
pip install git+https://github.com/asiffer/marc
```

## Get started

First you must init the database (migration)

```
marc migrate
```

Then you can start the server and visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

```
marc runserver
```

Then you can either add reports manually ("plus" button) or define search directories in the config panel (and trigger with the "blitz button").

![Config panel](/assets/config.png)

## Details

`marc` is a django app that basically uses the builtin dev server to run. The first aim was to build a local and personal app, not more.

Currently we cannot configure so much the app to run in "production" mode but that could be a next step if people are interested in.