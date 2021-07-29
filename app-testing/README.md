# Opentrons Executable End to End Testing

> The purpose of this folder is to allow tests to run against the Electron executable.

Slices of the release cycle tests will be selected as candidates for automation and then performed against the Opentrons run app executable on [Windows,Mac,Linux] and various robot configurations.


## Considerations

chromedriver against current electron version (see [package.json](../package.json))
$ chromedriver --version
ChromeDriver 76.0.3809.126 (d80a294506b4c9d18015e755cee48f953ddc3f2f-refs/branch-heads/3809@{#1024})
This must be on path

## Steps

1. Install the application
   1. https://opentrons.com/ot-app/
1. create .env from example.env
   1. fill in values
1. make test

## ToDo

- link to smartsheets tests
- screenshots
- reporting

## commands

use xdist
`pipenv run pytest -n3`
