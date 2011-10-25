'''
Created on Sep 28, 2010

@author: Jrula
'''

from mechanize import Browser
import time

b = Browser()

wings = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M"]
floors = ["G", 1, 2, 3, 4]
rooms = range(0,99)
f = open("rooms.txt", "w")

for wing in wings:
    for floor in floors:
        for room in rooms:
            
            roomstr = str(room)
            
            if len(roomstr) < 2:
                roomstr = "0%s" % roomstr
            
            page = b.open("http://www.mccormick.northwestern.edu/maps/roomfinder.php?room=%s%s%s" % (wing, floor, roomstr)).get_data()

            if page.find("We could not locate the room you specified") > 0:
                print "Room %s%s%s Not Found..." % (wing, floor, roomstr)
            else:
                #Room was found
                print "Found Room %s%s%s!" % (wing, floor, roomstr)
                f.write("%s%s%s\n" % (wing, floor, roomstr))
            
            #Delay so as not to get blacklisted
            time.sleep(1)

f.close()
            




