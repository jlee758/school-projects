
"""
FILE: skeleton_parser.py
------------------
Author: Firas Abuzaid (fabuzaid@stanford.edu)
Author: Perth Charernwattanagul (puch@stanford.edu)
Modified: 04/21/2014

Skeleton parser for CS564 programming project 1. Has useful imports and
functions for parsing, including:

1) Directory handling -- the parser takes a list of eBay json files
and opens each file inside of a loop. You just need to fill in the rest.
2) Dollar value conversions -- the json files store dollar value amounts in
a string like $3,453.23 -- we provide a function to convert it to a string
like XXXXX.xx.
3) Date/time conversions -- the json files store dates/ times in the form
Mon-DD-YY HH:MM:SS -- we wrote a function (transformDttm) that converts to the
for YYYY-MM-DD HH:MM:SS, which will sort chronologically in SQL.

Your job is to implement the parseJson function, which is invoked on each file by
the main function. We create the initial Python dictionary object of items for
you; the rest is up to you!
Happy parsing!
"""

import sys
from json import loads
from re import sub

columnSeparator = "|"

# Dictionary of months used for date transformation
MONTHS = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',\
        'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

"""
Returns true if a file ends in .json
"""
def isJson(f):
    return len(f) > 5 and f[-5:] == '.json'

"""
Converts month to a number, e.g. 'Dec' to '12'
"""
def transformMonth(mon):
    if mon in MONTHS:
        return MONTHS[mon]
    else:
        return mon

"""
Transforms a timestamp from Mon-DD-YY HH:MM:SS to YYYY-MM-DD HH:MM:SS
"""
def transformDttm(dttm):
    dttm = dttm.strip().split(' ')
    dt = dttm[0].split('-')
    date = '20' + dt[2] + '-'
    date += transformMonth(dt[0]) + '-' + dt[1]
    return date + ' ' + dttm[1]

"""
Transform a dollar value amount from a string like $3,453.23 to XXXXX.xx
"""

def transformDollar(money):
    if money == None or len(money) == 0:
        return money
    return sub(r'[^\d.]', '', money)

#define the entities
entityItems = {}
entityUsers = {}
entityCategories = {}
entityBids = []

#escape double quotes for when importing data into tables
def escapeQuote(str):
    if(str == None):
        return '"NULL"'
    else:
        return '"' + str.replace('"', '""') + '"'

"""
Parses a single json file. Currently, there's a loop that iterates over each
item in the data set. Your job is to extend this functionality to create all
of the necessary SQL tables for your database.
"""
def parseJson(json_file):
    with open(json_file, 'r') as f:
        items = loads(f.read())['Items'] # creates a Python dictionary of Items for the supplied json file
        for item in items:
            #Account for when buy_price is not present for some items
            if (item['ItemID'] not in entityItems):
                if ('Buy_Price' in item):
                    itemBuy = transformDollar(item['Buy_Price'])
                else:
                    itemBuy = 'NULL'

                #if an item is not already registered in the entity, then add it
                entityItems[item['ItemID']] = {
                    'ItemID': item['ItemID'],
                    'Name': escapeQuote(item['Name']), 
                    'Currently': transformDollar(item['Currently']),
                    'First_Bid': transformDollar(item['First_Bid']),
                    'Number_of_Bids': item['Number_of_Bids'],
                    'Buy_Price': itemBuy,
                    'Started': transformDttm(item['Started']),
                    'Ends': transformDttm(item['Ends']),
                    'Description': escapeQuote(item['Description']),
                    'UserID': item['Seller']['UserID']}

            #if the seller is not already a recognized user, then add it to the entity
            if (item['Seller']['UserID'] not in entityUsers):
                entityUsers[item['Seller']['UserID']] = {
                        'UserID': escapeQuote(item['Seller']['UserID']),
                        'Rating': item['Seller']['Rating'],
                        'Location': escapeQuote(item['Location']),
                        'Country': escapeQuote(item['Country'])}

            #if a category is not already present, then add it to the entity along with the item
            #else, if the item and category are not already present, then add them to the entity
            for category in item['Category']:
                if (category not in entityCategories):
                    entityCategories[category] = {'Items': [item['ItemID']], 'Category': escapeQuote(category)}
                elif (category in entityCategories and item['ItemID'] not in entityCategories[category]['Items']):
                    entityCategories[category]['Items'].append(item['ItemID'])

            #if bids are found for an item:
            if (item['Bids']):
                for bid in item['Bids']:
                    #add to the bids entity the current bid
                    entityBids.append(
                        {'ItemID': item['ItemID'],
                        'UserID': bid['Bid']['Bidder']['UserID'],
                        'Time': transformDttm(bid['Bid']['Time']),
                        'Amount': transformDollar(bid['Bid']['Amount'])})

                    #if a bidder is not already a seller, then update it in the users entity
                    if (bid['Bid']['Bidder']['UserID'] not in entityUsers):
                        #since location and country are not required, check if they are present
                        if ('Location' in bid['Bid']['Bidder']):
                            bidderLoc = bid['Bid']['Bidder']['Location']
                        else:
                            bidderLoc = 'NULL'
                        if ('Country' in bid['Bid']['Bidder']):
                            bidderCou = bid['Bid']['Bidder']['Country']
                        else:
                            bidderCou = 'NULL'

                        #update the users entity
                        entityUsers[bid['Bid']['Bidder']['UserID']] = {
                                'UserID': escapeQuote(bid['Bid']['Bidder']['UserID']),
                                'Rating': bid['Bid']['Bidder']['Rating'],
                                'Location': escapeQuote(bidderLoc),
                                'Country': escapeQuote(bidderCou)}
            pass

"""
Loops through each json files provided on the command line and passes each file
to the parser
"""
def main(argv):
    if len(argv) < 2:
        print >> sys.stderr, 'Usage: python skeleton_json_parser.py <path to json files>'
        sys.exit(1)

    # loops over all .json files in the argument
    for f in argv[1:]:
        if isJson(f):
            parseJson(f)
            print "Success parsing " + f
    
    #empty out items.dat
    open('items.dat', 'w').close()
    #write to items.dat contents of item entity
    fileItem = open('items.dat', 'a')
    for id, attributes in entityItems.iteritems():
        line = ''
        line += attributes['ItemID'] + columnSeparator
        line += attributes['Name'] + columnSeparator
        line += attributes['Currently'] + columnSeparator
        line += attributes['First_Bid'] + columnSeparator
        line += attributes['Number_of_Bids'] + columnSeparator
	line += attributes['Buy_Price'] + columnSeparator
        line += attributes['Started'] + columnSeparator
        line += attributes['Ends'] + columnSeparator
        line += attributes['UserID'] + columnSeparator
        line += str(attributes['Description']) + '\n'
        fileItem.write(line)
    fileItem.close()

    #empty out users.dat
    open('users.dat', 'w').close()
    #write to users.dat contents of users entity
    fileUsers = open('users.dat', 'a')
    for id, attributes in entityUsers.iteritems():
        line = ''
        line += attributes['UserID'] + columnSeparator
        line += attributes['Rating'] + columnSeparator
        line += attributes['Location'] + columnSeparator
        line += attributes['Country'] + '\n'
        fileUsers.write(line)
    fileUsers.close()

    #empty out categories.dat
    open('categories.dat', 'w').close()
    #write to categories.dat contents of category entity
    fileCat = open('categories.dat', 'a')
    for category in entityCategories:
        line = ''
        for item in entityCategories[category]['Items']:
            line += str(item) + columnSeparator + str(category) + '\n'
        fileCat.write(line)
    fileCat.close()

    #empty out bids.dat
    open('bids.dat', 'w').close()
    #write to bids.dat contents of bids entity
    fileBids = open('bids.dat', 'a')
    for attributes in entityBids:
        line = ''
        line += attributes['ItemID'] + columnSeparator
        line += attributes['UserID'] + columnSeparator
        line += attributes['Time'] + columnSeparator
        line += attributes['Amount'] + '\n'
        fileBids.write(line)
    fileBids.close()

if __name__ == '__main__':
    main(sys.argv)
