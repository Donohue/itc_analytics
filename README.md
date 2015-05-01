# iTunes Analytics

iTunes Analytics is a Python script that exports analytics from iTunes into CSV format.

# About

iTunes Analytics can be used as a stand-alone program or as part of another Python project.

The script works by performing the necessary web requests to log a developer into iTunes Connect, and use the returned authentication cookies to perform the invite web request.

*NOTE:* itc\_analytics.py requires your iTunes Connect password to complete the analytics request. If you use the script as part of another project you will need to store your iTunes Connect password somewhere it can be retrieved in plaintext in order to pass to the library. On the command line your iTunes Connect password is entered using the [getpass](https://docs.python.org/2/library/getpass.html) library, which allows you to enter your password using stdin without echoing the password on the command line.

## Use as a stand-alone program

Usage:

    python itc_analytics.py [measures|all-time|retention] <iTC login email> <App ID>

## Use as part of another script

Python:

    from itc_analytics import ITCAnalytics
    try:
        analytics = ITCAnalytics(<iTC email>, <iTC password>, <App ID>)
        analytics.print_retention()
    except Exception as e:
        print 'Oops! Something went wrong!'

# Credits

This script is heavily based off of the [appdailysales](https://github.com/kirbyt/appdailysales) project by [Kirby Turner](https://github.com/kirbyt) and friends.

