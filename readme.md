# BRIEF INSTRUCTIONS ON HOW TO MAKE THIS APP RUN
## To install in a virtual environment (recommended):
Python 3.x required.

## Unix/MacOS:
python3 -m venv venv
source venv/bin/activate
pip install h2o-wave

## Windows:
python -m venv venv
.\venv\Scripts\activate
pip install h2o-wave

## Run the main script.
wave main.py.

## Warning
In despite of warning messages instructing or suggesting to do that, don't delete "import appwrite" and "import wave". Otherwise the app won't work at all.

## Assorted notes
### Query limits:
_main.py, line 54_: The default page size for appwrite queries is 50. Not sure if bigger values can be passed thru de query directive Query.limit, but smaller values are for sure. If this value changes, it's suggested to reflect this change on the 'content' template, as well.
### Maximize query efficiency
On _line 55, main.py_ the _Query.is_no_null_ query parameter retrieves only those documents with data on the 'notes' field.

------
_This is a work in progress._

------
## TODO:
Config production url. For now, it runs on http://localhost:10101/customers.

------
## ABOUT THIS PROJECT:
This is a working project that can be used as a starting point for your own app, using appwrite as the backend and h2o-wave as a frontend interface for python code.
