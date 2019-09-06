import bs4
from bs4 import BeautifulSoup
import csv
from csv import writer

"""
AB: use this:
    '(past\s)*(family|forensic|medica(l|tion)|personal|psychiatr(ic|y)|social)(\s+and\s+(family|forensic|medical|personal|psychiatr(ic|y)|social))?\s+(background|history)'
"""

def stopcheck(c):
    if (c.name=="h1" or c.name=="h2" or c.name =='h6' or(c.name=="p" and \
        "histo" in c.text.lower() and len(c.text.lower())<80) or \
        (c.name=="b" and "histo" in c.text.lower() and \
         len(c.text.lower())<80) or (c.name=="p" and \
        "circum" in c.text.lower() and len(c.text.lower())<80) or \
        (c.name=="b" and "circum" in c.text.lower() and \
        len(c.text.lower())<80) or (c.name=="p" and ":" in c.text.lower() and \ 
        len(c.text.lower())<80) or (c.name=="b" and ":" in c.text.lower() and \
        len(c.text.lower())<80) or (c.name=="b" and "mental state" in c.text.lower() and \
        len(c.text.lower())<80) or (c.name=="p" and "mental state" in c.text.lower() and \
        len(c.text.lower())<80) or (c.name=="b" and "progress" in c.text.lower() and \
        len(c.text.lower())<80) or (c.name=="p" and "progress" in c.text.lower() and \
        len(c.text.lower())<80)):
        return True
    else:
        return False

def interiorcheck(checkpoint):
    parent = checkpoint.parent
    if parent.name == 'p' and len(parent.text)>100:
        return True
    else:
        return False

def freetextcheck(checkpoint):
    textset = checkpoint.text
    textsetlow = textset.text.lower()
    if "personal history\n" in textsetlow or "personal history:" in textsetlow or "personal history :" in textsetlow:
        return True

def parsethis(b):
    out = []
    soup = BeautifulSoup(b,'html.parser')
    a = soup.find_all(['h1','h2','h6','b','p'])
    for x in a:
        if "personal his" in x.text.lower() and len(x.text.lower()) < 80:
            if x.name != 'p':
                intcheck = interiorcheck(x)
            else:
                intcheck = False
            tagtext = ""
            if intcheck == True:
               # print x.parent.name
                findpoint = x.parent.text.find(x.text)
                totalindex = findpoint + len(x.text)
    
                #print findpoint
                #print len(x.text)
                #print totalindex
                #print x.parent.text[totalindex:]
                tagtext = x.parent.text[totalindex:]
                #print tagtext
                #print "BREAK "
                #print " "
            endpoint = False
            counter = 0
            y = x
            while endpoint == False:
                try:
                    if len(y.find_next().text) != len(y.text)-2 :
                        y = y.find_next()
                        counter = counter + 1
                        addpoint = True
                    else:
                        y = y.find_next()
                        addpoint = False
                except:
                    print("Error")
                    endpoint = True
                    break
                if stopcheck(y) == True or counter ==6:
                    endpoint = True
                    break
                else:
                    z = y.text.lower()
                    if len(z.strip()) > 1 and addpoint == True:
                        tagtext = tagtext + y.text.replace("\n","") + "\n"
            if len(tagtext)> 0:
                xout = x.text
                holder = [xout,tagtext]
                out.append(holder)
                holder = []
    return out
        